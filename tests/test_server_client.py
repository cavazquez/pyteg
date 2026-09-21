"""Tests para el módulo de cliente del servidor."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyteg.server.conexion.cliente import Client


class TestClienteEjecutarMensaje(unittest.TestCase):
    """Tests para Client.ejecutar_mensaje."""

    def _make_client(
        self,
        username: str = "TestUser",
        *,
        handshake_accepted: bool | None = True,
    ) -> tuple[Client, MagicMock]:
        conn = MagicMock()
        server = MagicMock()
        server.mapa = MagicMock()
        server.game = MagicMock()
        server.estado = MagicMock()
        server.estado.puede_ejecutar_accion.return_value = True
        server.estado.estado_actual.return_value = "jugando"
        client = Client(1, conn, server, username, soy_admin=False)
        if handshake_accepted is not None:
            client.marcar_handshake(handshake_accepted)
        return client, server

    def test_mensaje_desconocido_envia_error_estructurado(self) -> None:
        """Un comando no registrado no llega al manager de tareas."""
        client, _server = self._make_client()
        with patch.object(client.transmisor, "enviar_error") as enviar_error:
            client.ejecutar_mensaje({"mensaje": "noexiste"})
            enviar_error.assert_called_once_with(
                "unknown_message", "Mensaje desconocido: noexiste"
            )

    def test_payload_escalar_envia_error_sin_construir_tarea(self) -> None:
        """Un array JSON no provoca AttributeError ni cambia el servidor."""
        client, _server = self._make_client()
        with patch.object(client.transmisor, "enviar_error") as enviar_error:
            client.ejecutar_mensaje([])
            enviar_error.assert_called_once_with(
                "invalid_payload", "El comando debe ser un objeto JSON"
            )

    def test_mensaje_chat_se_encola_para_el_ejecutor(self) -> None:
        """El lector valida chat, pero deja su ejecución al serializador."""
        client, server = self._make_client("Fulano")
        payload = {"mensaje": "chat", "msg": "Hola"}

        client.ejecutar_mensaje(payload)

        server.encolar_comando.assert_called_once_with(client, payload)

    def test_comando_sin_handshake_envia_error_y_no_se_encola(self) -> None:
        """Un cliente TCP no puede operar antes de negociar el protocolo."""
        client, server = self._make_client(handshake_accepted=None)

        with patch.object(client.transmisor, "enviar_error") as enviar_error:
            client.ejecutar_mensaje({"mensaje": "chat", "msg": "antes"})

        enviar_error.assert_called_once_with(
            "handshake_required",
            "Esta conexión debe completar el handshake antes de enviar comandos.",
        )
        server.encolar_comando.assert_not_called()

    def test_limpiar_cache_comandos_descarta_resultados_y_payloads(self) -> None:
        """Una revancha no reutiliza idempotencia de la partida anterior."""
        client, _server = self._make_client()
        client.remember_command_result(
            "partida-1",
            {"command_id": "partida-1", "accepted": True, "revision": 2},
            {"mensaje": "set_username", "username": "Anterior"},
        )

        client.limpiar_cache_comandos()

        self.assertIsNone(client.command_result("partida-1"))
        self.assertIsNone(client.command_payload("partida-1"))
