"""Wrapper simple sobre sockets para el servidor."""

from __future__ import annotations

import queue
import select
import socket
import threading
import time

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.logger import get_logger

LOGGER = get_logger(__name__)
_RECEIVE_BUFFER_BYTES = 65_536
_MAX_PENDING_FRAMES = 128
_SEND_DEADLINE_SECONDS = 2.0


class ConnectionServer:
    """Wrapper para manejar la conexión de socket del servidor con un cliente."""

    def __init__(self, connection: socket.socket, addr: tuple[str, int]) -> None:
        """Inicializa la conexión del servidor.

        Args:
            connection: Socket de conexión.
            addr: Tupla con (host, puerto) de la dirección del cliente.

        """
        self._conn = connection
        self._addr = addr
        self._codec = NulDelimitedUtf8Codec()
        self._close_lock = threading.RLock()
        self._closed = False
        self._outgoing: queue.Queue[object] = queue.Queue(_MAX_PENDING_FRAMES)
        self._pending_lock = threading.Lock()
        self._pending_frames = 0
        self._outgoing_idle = threading.Event()
        self._outgoing_idle.set()
        self._writer_stop = threading.Event()
        self._writer_stopped = threading.Event()
        self._writer_thread: threading.Thread | None = None

    def receiver(self) -> list[str] | None:
        r"""Recibe datos del cliente.

        Returns:
            Lista de mensajes completos, ``[]`` si queda una trama parcial, o
            ``None`` ante EOF o un error de framing.

        """
        try:
            encode_data = self._conn.recv(_RECEIVE_BUFFER_BYTES)
            if not encode_data:
                try:
                    self._codec.finish()
                except FrameCodecError as error:
                    LOGGER.warning("EOF con trama TCP incompleta: %s", error)
                return None
        except ConnectionResetError:
            return None
        except BrokenPipeError as ex:
            LOGGER.warning("BrokenPipeError al recibir: %s", ex)
            return None
        except (ConnectionError, OSError) as ex:
            LOGGER.warning("Error de socket al recibir: %s", ex)
            return None

        try:
            messages = self._codec.feed(encode_data)
        except FrameCodecError as error:
            LOGGER.warning("Trama TCP inválida de %s: %s", self._addr, error)
            self.close()
            return None

        LOGGER.debug(
            "Recibidos %s bytes de %s; %s trama(s) completa(s), %s pendiente(s)",
            len(encode_data),
            self._addr,
            len(messages),
            self._codec.pending_bytes,
        )
        return messages

    def send(self, data: str) -> None:
        """Encola datos al cliente sin bloquear la transición de juego.

        Args:
            data: Datos a enviar.

        """
        LOGGER.debug("Enviando %s", data)
        encode_data = NulDelimitedUtf8Codec.encode_frame(data)
        queue_full = False
        with self._close_lock:
            if self._closed:
                return
            try:
                self._start_writer_locked()
                self._mark_frame_pending()
                self._outgoing.put_nowait(encode_data)
            except queue.Full:
                self._mark_frame_complete()
                queue_full = True

        if queue_full:
            LOGGER.warning(
                "La cola de salida de %s alcanzó %s tramas; se desconecta",
                self._addr,
                _MAX_PENDING_FRAMES,
            )
            self.close(wait_for_writer=False)

    def _start_writer_locked(self) -> None:
        """Inicia el escritor FIFO al enviar la primera trama.

        Debe llamarse con ``_close_lock`` tomado.
        """
        if self._writer_thread is not None:
            return
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name=f"pyteg-socket-writer-{self._addr[0]}:{self._addr[1]}",
            daemon=True,
        )
        self._writer_thread.start()

    def _writer_loop(self) -> None:
        """Escribe tramas FIFO hasta cerrar o detectar un cliente lento."""
        try:
            while not self._writer_stop.is_set():
                try:
                    item = self._outgoing.get(timeout=0.1)
                except queue.Empty:
                    continue

                try:
                    if isinstance(item, bytes) and not self._send_frame(item):
                        return
                finally:
                    self._outgoing.task_done()
                    self._mark_frame_complete()
        finally:
            self._writer_stopped.set()

    def flush_outgoing(self, timeout: float = _SEND_DEADLINE_SECONDS) -> bool:
        """Espera de forma acotada a que el escritor entregue lo ya encolado.

        Args:
            timeout: Máximo de segundos para vaciar las tramas pendientes.

        Returns:
            ``True`` cuando todas las tramas encoladas se entregaron antes del
            plazo.

        """
        return self._outgoing_idle.wait(timeout)

    def _mark_frame_pending(self) -> None:
        """Registra una trama pendiente para el drenaje explícito."""
        with self._pending_lock:
            self._pending_frames += 1
            self._outgoing_idle.clear()

    def _mark_frame_complete(self) -> None:
        """Marca una trama enviada o descartada y despierta a quien drena."""
        with self._pending_lock:
            self._pending_frames -= 1
            if self._pending_frames == 0:
                self._outgoing_idle.set()

    def _send_frame(self, frame: bytes) -> bool:
        """Envía una trama completa antes del plazo máximo configurado.

        Returns:
            ``True`` si la trama llegó al socket; ``False`` al cerrar o vencer
            el plazo de escritura.

        """
        deadline = time.monotonic() + _SEND_DEADLINE_SECONDS
        remaining_data = memoryview(frame)
        sent_completely = True
        while remaining_data and sent_completely:
            with self._close_lock:
                if self._closed:
                    sent_completely = False
                    break

            remaining_seconds = deadline - time.monotonic()
            if remaining_seconds <= 0:
                LOGGER.warning("Venció el plazo de envío hacia %s", self._addr)
                self.close()
                sent_completely = False
                break

            try:
                _readable, writable, _exceptional = select.select(
                    [], [self._conn], [], remaining_seconds
                )
            except AttributeError, TypeError, ValueError:
                sent_completely = self._send_frame_without_select(remaining_data)
                break
            except OSError as error:
                LOGGER.warning("Error esperando socket escribible: %s", error)
                self.close()
                sent_completely = False
                break

            if not writable:
                LOGGER.warning("Cliente lento al enviar hacia %s", self._addr)
                self.close()
                sent_completely = False
                break

            try:
                sent = self._conn.send(remaining_data)
            except (ConnectionError, OSError) as error:
                LOGGER.warning("Error de socket al enviar: %s", error)
                self.close()
                sent_completely = False
                break

            if sent <= 0:
                LOGGER.warning("El socket no aceptó datos hacia %s", self._addr)
                self.close()
                sent_completely = False
                break
            remaining_data = remaining_data[sent:]

        return sent_completely

    def _send_frame_without_select(self, frame: memoryview) -> bool:
        """Compatibilidad para dobles de socket sin descriptor seleccionable.

        Returns:
            ``True`` si el doble aceptó la trama completa.

        """
        try:
            self._conn.sendall(bytes(frame))
        except (ConnectionError, OSError) as error:
            LOGGER.warning("Error de socket al enviar: %s", error)
            self.close()
            return False
        return True

    def close(self, *, wait_for_writer: bool = True) -> None:
        """Cierra la conexión con el cliente una única vez.

        Args:
            wait_for_writer: Espera al escritor salvo al rechazar una cola llena
                desde la transición de juego.

        """
        with self._close_lock:
            was_open = not self._closed
            self._closed = True
            self._writer_stop.set()
            writer_thread = self._writer_thread

        if was_open:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                try:
                    self._conn.close()
                except OSError as ex:
                    LOGGER.warning("Error al cerrar conexión: %s", ex)

        if (
            wait_for_writer
            and writer_thread is not None
            and threading.current_thread() is not writer_thread
        ):
            writer_thread.join(timeout=_SEND_DEADLINE_SECONDS + 0.5)
