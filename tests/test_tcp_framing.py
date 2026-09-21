"""Regresiones del framing JSON + NUL usado por las conexiones TCP."""

# ruff: noqa: N802 -- el doble reproduce los nombres de la API de QTcpSocket.

from __future__ import annotations

import json
import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, call, patch

from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import QApplication

from pyteg.client.conexion.connection import ConnectionClient
from pyteg.codecs_utils import (
    FrameTooLargeError,
    IncompleteFrameError,
    NulDelimitedUtf8Codec,
)
from pyteg.server.conexion.connection import ConnectionServer

if TYPE_CHECKING:
    import socket
    from collections.abc import Callable


class _FakeSocket:
    """Socket mínimo con chunks programados para probar el adaptador servidor."""

    def __init__(self, chunks: list[bytes]) -> None:
        """Inicializa el socket con los bytes que devolverá ``recv``."""
        self._chunks = list(chunks)
        self.closed = False
        self.shutdown_called = False

    def recv(self, _: int) -> bytes:
        """Devuelve el siguiente chunk o EOF.

        Returns:
            El siguiente bloque de bytes o ``b""`` al terminar.

        """
        if self._chunks:
            return self._chunks.pop(0)
        return b""

    def shutdown(self, _: int) -> None:
        """Registra que el adaptador pidió cerrar el socket."""
        self.shutdown_called = True

    def close(self) -> None:
        """Registra el cierre del socket."""
        self.closed = True


class _FakeSignal:
    """Señal Qt mínima que registra el callback conectado."""

    def __init__(self) -> None:
        """Inicializa la señal vacía."""
        self.callback: Callable[..., None] | None = None

    def connect(self, callback: Callable[..., None]) -> None:
        """Registra un callback igual que una señal Qt."""
        self.callback = callback


class _FakeQtSocket:
    """Doble de QTcpSocket con chunks para probar ``ConnectionClient``."""

    def __init__(self, chunks: list[bytes]) -> None:
        """Inicializa las señales y los bytes pendientes."""
        self.readyRead = _FakeSignal()
        self.errorOccurred = _FakeSignal()
        self.stateChanged = _FakeSignal()
        self.connected = _FakeSignal()
        self._chunks = list(chunks)
        self.disconnected = False
        self.sent: list[bytes] = []

    def bytesAvailable(self) -> int:
        """Devuelve bytes disponibles en el chunk actual.

        Returns:
            Cantidad de bytes disponibles.

        """
        return len(self._chunks[0]) if self._chunks else 0

    def readAll(self) -> bytes:
        """Devuelve el próximo chunk como haría QTcpSocket.

        Returns:
            El siguiente bloque de bytes.

        """
        return self._chunks.pop(0)

    def disconnectFromHost(self) -> None:
        """Registra una desconexión solicitada."""
        self.disconnected = True

    def write(self, data: bytes) -> None:
        """Registra bytes enviados por el cliente."""
        self.sent.append(data)

    def state(self) -> QAbstractSocket.SocketState:
        """Informa un socket conectado para las consultas del adaptador.

        Returns:
            El estado conectado de QAbstractSocket.

        """
        return QAbstractSocket.SocketState.ConnectedState


class TestNulDelimitedUtf8Codec(unittest.TestCase):
    """Prueba el codec incremental compartido por servidor y cliente Qt."""

    def test_reassembles_every_split_position_including_multibyte_utf8(self) -> None:
        """Cada corte posible devuelve el mismo mensaje completo una sola vez."""
        message = json.dumps({"mensaje": "chat", "msg": "café ☕"}, ensure_ascii=False)
        frame = NulDelimitedUtf8Codec.encode_frame(message)

        for split_at in range(1, len(frame)):
            with self.subTest(split_at=split_at):
                codec = NulDelimitedUtf8Codec()
                self.assertEqual(codec.feed(frame[:split_at]), [])
                self.assertEqual(codec.feed(frame[split_at:]), [message])
                codec.finish()

    def test_returns_multiple_complete_frames_from_one_chunk(self) -> None:
        """Un solo recv puede contener varias tramas consecutivas."""
        first = '{"mensaje":"uno"}'
        second = '{"mensaje":"dos"}'
        codec = NulDelimitedUtf8Codec()

        result = codec.feed(
            NulDelimitedUtf8Codec.encode_frame(first)
            + NulDelimitedUtf8Codec.encode_frame(second)
        )

        self.assertEqual(result, [first, second])
        self.assertEqual(codec.pending_bytes, 0)

    def test_accepts_frames_larger_than_old_socket_read_size(self) -> None:
        """Una trama válida de más de 1024 bytes se conserva completa."""
        message = json.dumps({"mensaje": "chat", "msg": "x" * 4_096})
        frame = NulDelimitedUtf8Codec.encode_frame(message)
        codec = NulDelimitedUtf8Codec()

        self.assertEqual(codec.feed(frame[:512]), [])
        self.assertEqual(codec.feed(frame[512:2_048]), [])
        self.assertEqual(codec.feed(frame[2_048:]), [message])

    def test_rejects_oversized_unterminated_frame(self) -> None:
        """El buffer no puede crecer sin límite si falta el delimitador."""
        codec = NulDelimitedUtf8Codec(max_frame_bytes=3)

        with self.assertRaises(FrameTooLargeError):
            codec.feed(b"abcd")

    def test_eof_with_partial_frame_does_not_emit_a_message(self) -> None:
        """Una trama truncada al cerrar el peer se rechaza explícitamente."""
        codec = NulDelimitedUtf8Codec()
        self.assertEqual(codec.feed(b'{"mensaje":"chat"'), [])

        with self.assertRaises(IncompleteFrameError):
            codec.finish()


class TestTcpConnectionFraming(unittest.TestCase):
    """Prueba que ambos adaptadores usan el codec incremental compartido."""

    _app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        """Crea la aplicación Qt necesaria para instanciar el widget cliente."""
        existing_app = QApplication.instance()
        cls._app = (
            cast("QApplication", existing_app)
            if existing_app is not None
            else QApplication([])
        )

    def test_server_adapter_keeps_fragment_until_delimiter(self) -> None:
        """El adaptador del servidor no trata un fragmento como EOF."""
        message = json.dumps({"mensaje": "chat", "msg": "café"}, ensure_ascii=False)
        frame = NulDelimitedUtf8Codec.encode_frame(message)
        fake_socket = _FakeSocket([frame[:15], frame[15:]])
        connection = ConnectionServer(
            cast("socket.socket", fake_socket), ("127.0.0.1", 12345)
        )

        self.assertEqual(connection.receiver(), [])
        self.assertEqual(connection.receiver(), [message])

    @patch("pyteg.client.conexion.connection.QTcpSocket")
    @patch("pyteg.client.conexion.connection.ClientTaskManager.msg_to_task")
    def test_qtcp_adapter_reassembles_fragmented_utf8(
        self,
        msg_to_task: MagicMock,
        qtcp_socket: MagicMock,
    ) -> None:
        """El slot de QTcpSocket entrega JSON sólo después de una trama completa."""
        payload = {"mensaje": "chat", "msg": "café"}
        frame = NulDelimitedUtf8Codec.encode_frame(
            json.dumps(payload, ensure_ascii=False)
        )
        split_at = frame.index("é".encode()) + 1
        fake_socket = _FakeQtSocket([frame[:split_at], frame[split_at:]])
        qtcp_socket.return_value = fake_socket
        first_task = MagicMock()
        msg_to_task.return_value = first_task

        connection = ConnectionClient(MagicMock())
        connection.read_data()

        self.assertEqual(msg_to_task.call_args_list, [call(payload)])
        first_task.run.assert_called_once()
        self.assertFalse(fake_socket.disconnected)

    @patch("pyteg.client.conexion.connection.QTcpSocket")
    @patch("pyteg.client.conexion.connection.ClientTaskManager.msg_to_task")
    def test_qtcp_adapter_ignores_invalid_messages_and_keeps_reading(
        self,
        msg_to_task: MagicMock,
        qtcp_socket: MagicMock,
    ) -> None:
        """Un texto o JSON inválido no detiene los eventos válidos posteriores."""
        valid_payload = {"mensaje": "chat", "msg": "sigo conectado"}
        fake_socket = _FakeQtSocket([
            NulDelimitedUtf8Codec.encode_frame("El juego ya está en progreso")
            + NulDelimitedUtf8Codec.encode_frame("[]")
            + NulDelimitedUtf8Codec.encode_frame(json.dumps(valid_payload))
        ])
        qtcp_socket.return_value = fake_socket
        valid_task = MagicMock()
        msg_to_task.return_value = valid_task

        connection = ConnectionClient(MagicMock())
        connection.read_data()

        self.assertEqual(msg_to_task.call_args_list, [call(valid_payload)])
        valid_task.run.assert_called_once()
        self.assertFalse(fake_socket.disconnected)
