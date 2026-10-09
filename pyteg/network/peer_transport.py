"""Puerto TCP simétrico para acuerdos y sincronización entre participantes."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

import json
import socket
import threading
import time
from typing import TYPE_CHECKING, Any

from pyteg.codecs_utils import NulDelimitedUtf8Codec
from pyteg.persistence.archive import MAX_ARCHIVE_BYTES, canonical_bytes

if TYPE_CHECKING:
    from collections.abc import Callable

_TIMEOUT = 3.0
_READ_SIZE = 64 * 1024
_CONNECTIONS = 16


def _receive(connection: socket.socket) -> dict[str, Any]:
    codec = NulDelimitedUtf8Codec(MAX_ARCHIVE_BYTES)
    while chunk := connection.recv(_READ_SIZE):
        frames = codec.feed(chunk)
        if frames:
            message = json.loads(frames[0])
            if not isinstance(message, dict):
                raise ValueError("El mensaje de pares debe ser un objeto")
            return message
    raise ConnectionError("La conexión terminó antes de completar el mensaje")


def exchange(address: tuple[str, int], request: dict[str, Any]) -> dict[str, Any]:
    """Envía una petición acotada y espera exactamente una respuesta."""
    raw = canonical_bytes(request)
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("La transición excede el tamaño permitido")
    with socket.create_connection(address, timeout=_TIMEOUT) as connection:
        connection.settimeout(_TIMEOUT)
        connection.sendall(raw + b"\0")
        response = _receive(connection)
        if response.get("error"):
            raise ValueError(str(response["error"]))
        return response


class PeerPort:
    """Cada participante escucha peticiones; ninguno enruta toda la partida."""

    def __init__(
        self,
        handler: Callable[[dict[str, Any], str], dict[str, Any]],
        *,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        """Reserva el puerto y prepara límites de tiempo y concurrencia."""
        self._handler = handler
        self._stop = threading.Event()
        self._slots = threading.BoundedSemaphore(_CONNECTIONS)
        self._workers: set[threading.Thread] = set()
        self._lock = threading.Lock()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((host, port))
            self._socket.listen(_CONNECTIONS)
            self._socket.settimeout(0.2)
        except Exception:
            self._socket.close()
            raise
        self.port = int(self._socket.getsockname()[1])
        self._thread = threading.Thread(
            target=self._run, name="pyteg-peer-port", daemon=True
        )

    def start(self) -> None:
        """Arranca la recepción fuera del hilo de Qt."""
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                connection, address = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            if not self._slots.acquire(blocking=False):
                connection.close()
                continue
            worker = threading.Thread(
                target=self._serve,
                args=(connection, address[0]),
                name="pyteg-peer-request",
                daemon=True,
            )
            with self._lock:
                self._workers.add(worker)
            worker.start()

    def _serve(self, connection: socket.socket, host: str) -> None:
        try:
            with connection:
                connection.settimeout(_TIMEOUT)
                try:
                    response = self._handler(_receive(connection), host)
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    ConnectionError,
                    RecursionError,
                ) as error:
                    response = {"error": str(error)}
                raw = canonical_bytes(response)
                if len(raw) > MAX_ARCHIVE_BYTES:
                    raw = canonical_bytes({
                        "error": "La copia excede el tamaño permitido"
                    })
                connection.sendall(raw + b"\0")
        except OSError:
            pass
        finally:
            with self._lock:
                self._workers.discard(threading.current_thread())
            self._slots.release()

    def close(self) -> None:
        """Libera escucha y conexiones con esperas limitadas."""
        self._stop.set()
        self._socket.close()
        if self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)
        with self._lock:
            workers = tuple(self._workers)
        deadline = time.monotonic() + _TIMEOUT + 1
        for worker in workers:
            if worker is not threading.current_thread():
                worker.join(timeout=max(0, deadline - time.monotonic()))
