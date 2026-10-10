"""Puerto TCP simétrico para acuerdos y sincronización entre participantes."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

import socket
import threading
import time
from typing import TYPE_CHECKING, Any

from pyteg.network.identity import Identity
from pyteg.network.security import (
    TlsCredentials,
    connect_tls,
    proof,
    receive_authenticated,
    receive_json,
    send_json,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_TIMEOUT = 3.0
_CONNECTIONS = 16


def exchange(
    address: tuple[str, int],
    request: dict[str, Any],
    *,
    identity: Identity | None = None,
    expected_key: str | None = None,
    timeout: float = _TIMEOUT,
) -> dict[str, Any]:
    """Verifica el destino TLS y firma una petición ligada a su desafío nuevo."""
    if identity is None or expected_key is None:
        raise ValueError(
            "La conexión requiere una identidad y una invitación verificable"
        )
    with connect_tls(address, expected_key, timeout) as connection:
        connection.settimeout(timeout)
        greeting = receive_json(connection, limit=4096)
        send_json(connection, proof(identity, greeting, request))
        response = receive_json(connection)
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
        identity: Identity | None = None,
    ) -> None:
        """Reserva el puerto y prepara límites de tiempo y concurrencia."""
        self._handler = handler
        self._tls = TlsCredentials(identity or Identity())
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
            with self._tls.accept(connection) as secure:
                secure.settimeout(_TIMEOUT)
                try:
                    response = self._handler(receive_authenticated(secure), host)
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    ConnectionError,
                    RecursionError,
                ) as error:
                    response = {"error": str(error)}
                send_json(secure, response)
        except OSError:
            pass
        finally:
            connection.close()
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
