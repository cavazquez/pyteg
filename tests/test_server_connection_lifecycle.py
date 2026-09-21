"""Regresiones del ciclo de vida de conexiones del servidor."""

from __future__ import annotations

import json
import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

from pyteg.server.app import Server
from pyteg.server.conexion.cliente import Client

if TYPE_CHECKING:
    from pyteg.colores import IColor


class _FakeLobbyClient:
    """Doble mínimo para probar el registro y los colores del servidor."""

    def __init__(self, user_id: int) -> None:
        """Inicializa el jugador sin color asignado."""
        self._user_id = user_id
        self._color: IColor | None = None

    def asignar_color(self, color: IColor | None) -> None:
        """Guarda el color reservado por el servidor."""
        self._color = color

    def color_actual(self) -> IColor | None:
        """Devuelve el color que tiene reservado el jugador.

        Returns:
            Color reservado, si existe.

        """
        return self._color

    def userid(self) -> int:
        """Devuelve el ID del jugador.

        Returns:
            ID del jugador.

        """
        return self._user_id

    def username(self) -> str:
        """Devuelve un nombre para el broadcaster.

        Returns:
            Nombre visible del jugador.

        """
        return f"Jugador_{self._user_id}"


class TestClientCleanup(unittest.TestCase):
    """Asegura que el objeto Client libera recursos aun ante fallos."""

    def test_cerrar_is_idempotent(self) -> None:
        """Dos cierres no duplican el cierre físico ni la baja del registro."""
        connection = MagicMock()
        server = MagicMock()
        client = Client(1, connection, server, "Jugador", soy_admin=False)

        client.cerrar()
        client.cerrar()

        connection.close.assert_called_once_with()
        server.quitarme.assert_called_once_with(1, client)

    def test_run_cleans_up_after_handler_failure(self) -> None:
        """Un fallo inesperado de una tarea no deja socket ni registro vivos."""
        connection = MagicMock()
        connection.receiver.return_value = [
            json.dumps({"mensaje": "chat", "msg": "hola"})
        ]
        server = MagicMock()
        server.color.colores.return_value = []
        server.estado.estado_actual.return_value = "Inicial"
        client = Client(1, connection, server, "Jugador", soy_admin=False)

        with patch.object(client, "ejecutar_mensaje", side_effect=RuntimeError("boom")):
            client.run()

        connection.close.assert_called_once_with()
        server.quitarme.assert_called_once_with(1, client)


class TestServerLobbyCleanup(unittest.TestCase):
    """Comprueba que el servidor devuelve colores y evita sobreasignaciones."""

    def test_lobby_disconnect_returns_color_once(self) -> None:
        """La baja repetida no deja colores reservados ni jugadores fantasma."""
        server = Server()
        self.addCleanup(server.detener)
        client = _FakeLobbyClient(1)

        self.assertTrue(server.registrar_cliente(1, cast("Client", client)))
        self.assertEqual(len(server.color.colores_disponibles()), 7)

        server.quitarme(1)
        server.quitarme(1)

        self.assertEqual(server.cant_clients(), 0)
        self.assertEqual(server.dame_clientes(), [])
        self.assertEqual(len(server.color.colores_disponibles()), 8)

    def test_registration_rejects_ninth_client_without_reserving_color(self) -> None:
        """La novena conexión no reemplaza ni consume el color de otro jugador."""
        server = Server()
        self.addCleanup(server.detener)
        clients = [_FakeLobbyClient(user_id) for user_id in range(1, 10)]

        for client in clients[:8]:
            self.assertTrue(
                server.registrar_cliente(client.userid(), cast("Client", client))
            )

        self.assertFalse(server.registrar_cliente(9, cast("Client", clients[8])))
        self.assertEqual(server.cant_clients(), 8)
        self.assertEqual(len(server.color.colores_disponibles()), 0)
        self.assertIsNone(clients[8].color_actual())
