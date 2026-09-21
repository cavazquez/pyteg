"""Regresiones para la autoridad de sala durante el ciclo de una partida."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyteg.server.app import Server
from pyteg.server.conexion.cliente import Client


class TestServerAdminSuccession(unittest.TestCase):
    """La sucesión mantiene una única autoridad y respeta el registro."""

    def setUp(self) -> None:
        """Construye una sala con tres clientes en orden de registro."""
        self.server = Server()
        self.addCleanup(self.server.detener)
        self.clients = [
            Client(
                user_id,
                MagicMock(),
                self.server,
                f"Jugador_{user_id}",
                soy_admin=user_id == 1,
            )
            for user_id in range(1, 4)
        ]
        for client in self.clients:
            self.assertTrue(self.server.registrar_cliente(client.userid(), client))

    def _start_game_without_game_object(self) -> None:
        """Avanza el estado para probar autoridad sin asignar un mapa."""
        self.assertTrue(self.server.estado.esperar_jugadores())
        self.assertTrue(self.server.estado.empezar_partida())

    def _admin_ids(self) -> list[int]:
        """Devuelve los administradores actualmente conectados.

        Returns:
            IDs de los administradores conectados.

        """
        return [
            int(client.userid())
            for client in self.server.dame_clientes()
            if client.es_admin()
        ]

    def test_desconexion_del_admin_deja_sucesor_pendiente_hasta_final(self) -> None:
        """La baja en JUGANDO no entrega controles de lobby antes de tiempo."""
        self._start_game_without_game_object()
        with patch.object(self.server, "encolar_desconexion_jugador") as queued:
            self.server.quitarme(1, self.clients[0])

        queued.assert_called_once_with(1)
        self.assertEqual(self._admin_ids(), [])
        self.assertTrue(self.server.finalizar_partida())
        self.assertEqual(self._admin_ids(), [2])

    def test_eliminacion_del_admin_y_dos_bajas_eligen_el_siguiente(self) -> None:
        """Eliminación y desconexión sucesivas no crean dos administradores."""
        self._start_game_without_game_object()
        self.server.administrador_eliminado(1)
        self.assertEqual(self._admin_ids(), [])

        # Una eliminación real durante JUGANDO deja sucesor pendiente sólo
        # cuando el administrador estaba conectado; este caso comprueba que
        # una baja posterior del sucesor también rota la autoridad.
        self.server.quitarme(2, self.clients[1])
        self.assertEqual(self._admin_ids(), [])
        self.assertTrue(self.server.finalizar_partida())
        self.assertEqual(self._admin_ids(), [3])

    def test_revancha_conserva_al_sucesor_y_no_duplica_autoridad(self) -> None:
        """La autoridad elegida en FINALIZADO se conserva al volver al lobby."""
        self._start_game_without_game_object()
        with patch.object(self.server, "encolar_desconexion_jugador"):
            self.server.quitarme(1, self.clients[0])
        self.assertTrue(self.server.finalizar_partida())
        self.assertEqual(self._admin_ids(), [2])

        self.assertTrue(self.server.volver_al_lobby())
        self.assertEqual(self._admin_ids(), [2])
