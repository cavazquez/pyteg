"""Tests para el módulo de cliente del servidor."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyteg.server.conexion.cliente import Client


class TestClienteEjecutarMensaje(unittest.TestCase):
    """Tests para Client.ejecutar_mensaje."""

    def _make_client(self, username: str = "TestUser") -> tuple[Client, MagicMock]:
        conn = MagicMock()
        server = MagicMock()
        server.mapa = MagicMock()
        server.game = MagicMock()
        server.estado = MagicMock()
        server.estado.puede_ejecutar_accion.return_value = True
        server.estado.estado_actual.return_value = "jugando"
        client = Client(1, conn, server, username, soy_admin=False)
        return client, server

    def test_mensaje_desconocido_envia_error_chat(self) -> None:
        """Un mensaje no registrado se traduce en error vía transmisor."""
        client, _server = self._make_client()
        with (
            patch.object(
                client.transmisor, "enviar_error_chat", autospec=True
            ) as enviar_error,
            patch("pyteg.server.tasks.LOGGER.warning"),
        ):
            client.ejecutar_mensaje({"mensaje": "noexiste"})
            enviar_error.assert_called()

    def test_mensaje_chat_llama_enviar_chat(self) -> None:
        """El mensaje de chat reenvía el texto al broadcast del servidor."""
        client, server = self._make_client("Fulano")
        client.ejecutar_mensaje({"mensaje": "chat", "msg": "Hola"})
        server.enviar_chat.assert_called_once_with("Fulano", "Hola")
