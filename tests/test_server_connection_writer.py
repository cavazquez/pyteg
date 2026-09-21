"""Regresiones del escritor FIFO por conexión del servidor."""

from __future__ import annotations

import socket
import threading
import unittest
from typing import cast
from unittest.mock import patch

from pyteg.codecs_utils import NulDelimitedUtf8Codec
from pyteg.server.conexion.connection import ConnectionServer


class _BlockingSocket:
    """Doble de socket cuyo primer envío se detiene hasta que el test lo libera."""

    def __init__(self) -> None:
        """Inicializa las señales y el estado de cierre."""
        self.sending = threading.Event()
        self.release = threading.Event()
        self.closed = False

    def sendall(self, _: bytes) -> None:
        """Bloquea el escritor sin bloquear a quien encoló la trama."""
        self.sending.set()
        self.release.wait(timeout=2.0)

    def shutdown(self, _: int) -> None:
        """Acepta el shutdown que ejecuta el adaptador."""

    def close(self) -> None:
        """Registra el cierre solicitado por el adaptador."""
        self.closed = True


class TestConnectionServerWriter(unittest.TestCase):
    """El escritor conserva orden y corta conexiones incapaces de drenar la cola."""

    _EXPECTED_MESSAGES = 2

    def test_writer_preserves_complete_frame_order(self) -> None:
        """Dos envíos se reciben como tramas completas y en el mismo orden FIFO."""
        server_socket, peer_socket = socket.socketpair()
        peer_socket.settimeout(1.0)
        connection = ConnectionServer(server_socket, ("local", 1))
        codec = NulDelimitedUtf8Codec()

        try:
            connection.send('{"mensaje":"primero"}')
            connection.send('{"mensaje":"segundo"}')

            received: list[str] = []
            while len(received) < self._EXPECTED_MESSAGES:
                received.extend(codec.feed(peer_socket.recv(1024)))

            self.assertEqual(
                received,
                ['{"mensaje":"primero"}', '{"mensaje":"segundo"}'],
            )
        finally:
            connection.close()
            peer_socket.close()

        self.assertTrue(connection._writer_stopped.is_set())  # noqa: SLF001

    @patch("pyteg.server.conexion.connection._MAX_PENDING_FRAMES", 2)
    def test_full_queue_disconnects_a_slow_client_without_blocking_sender(self) -> None:
        """Al llenarse la cola, el productor cierra el socket sin esperar sendall."""
        socket_double = _BlockingSocket()
        connection = ConnectionServer(
            cast("socket.socket", socket_double), ("127.0.0.1", 32123)
        )

        try:
            connection.send("uno")
            self.assertTrue(
                socket_double.sending.wait(timeout=1.0),
                "El escritor no tomó la primera trama",
            )
            connection.send("dos")
            connection.send("tres")
            connection.send("cuatro")

            self.assertTrue(socket_double.closed, "La cola llena no cerró el socket")
        finally:
            socket_double.release.set()
            connection.close()

        self.assertTrue(
            connection._writer_stopped.wait(timeout=1.0),  # noqa: SLF001
            "El escritor no terminó después del cierre",
        )
