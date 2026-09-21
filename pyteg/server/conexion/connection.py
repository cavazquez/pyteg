"""Wrapper simple sobre sockets para el servidor."""

from __future__ import annotations

import socket
import threading

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.logger import get_logger

LOGGER = get_logger(__name__)
_RECEIVE_BUFFER_BYTES = 65_536


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
        """Envía datos al cliente.

        Args:
            data: Datos a enviar.

        """
        LOGGER.debug("Enviando %s", data)
        encode_data = NulDelimitedUtf8Codec.encode_frame(data)
        with self._close_lock:
            if self._closed:
                return
            try:
                self._conn.sendall(encode_data)
            except BrokenPipeError as ex:
                LOGGER.warning("BrokenPipeError al enviar: %s", ex)
                self.close()
            except (ConnectionError, OSError) as ex:
                LOGGER.warning("Error de socket al enviar: %s", ex)
                self.close()

    def close(self) -> None:
        """Cierra la conexión con el cliente una única vez."""
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                try:
                    self._conn.close()
                except OSError as ex:
                    LOGGER.warning("Error al cerrar conexión: %s", ex)
