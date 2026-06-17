"""Tests de tareas del cliente en lobby: estado y jugadores."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from PySide6.QtGui import QColor

from pyteg.client.app import Client
from pyteg.client.tasks.lobby.estado import ClientTaskEstado
from pyteg.client.tasks.lobby.jugadores import (
    ClientTaskActualizarListaJugadores,
    ClientTaskUserId,
    ClientTaskUsername,
)

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol
    from pyteg.client.tasks.types import (
        ActualizarListaJugadoresTaskData,
        EstadoTaskData,
        UserIdTaskData,
        UsernameTaskData,
    )


def _fake_main_window() -> SimpleNamespace:
    """Ventana mínima conforme a lo que usan las tareas de lobby.

    Returns:
        Host con `client`, `colores`, callbacks y `client_by_id` vacío.

    """
    client = Client()
    colores = MagicMock()
    colores.colores_asignados.return_value = {}
    return SimpleNamespace(
        client=client,
        client_by_id={},
        colores=colores,
        w=None,
        update_game_state=MagicMock(),
        ventana_esperar_jugadores=MagicMock(),
        update_player_list=MagicMock(),
        update_mi_jugador_info=MagicMock(),
        update=MagicMock(),
    )


class TestClientTaskEstado(unittest.TestCase):
    """Actualización de estado y transiciones de ventana."""

    def test_esperar_jugadores_abre_ventana(self) -> None:
        """El estado EsperarJugadores muestra la ventana de espera."""
        main_window = _fake_main_window()
        task = ClientTaskEstado(
            cast("EstadoTaskData", {"mensaje": "estado", "estado": "EsperarJugadores"})
        )

        task.run(cast("GameWindowProtocol", main_window))

        main_window.update_game_state.assert_called_once_with("EsperarJugadores")
        main_window.ventana_esperar_jugadores.assert_called_once()
        main_window.update.assert_not_called()

    def test_estado_generico_solo_actualiza_barra(self) -> None:
        """Otros estados solo llaman a `update_game_state`."""
        main_window = _fake_main_window()
        task = ClientTaskEstado(
            cast("EstadoTaskData", {"mensaje": "estado", "estado": "INICIAL"})
        )

        task.run(cast("GameWindowProtocol", main_window))

        main_window.update_game_state.assert_called_once_with("INICIAL")
        main_window.ventana_esperar_jugadores.assert_not_called()

    def test_jugando_cierra_ventana_espera_y_refresca(self) -> None:
        """JUGANDO cierra `w`, actualiza jugadores y repinta."""
        main_window = _fake_main_window()
        ventana = MagicMock()
        main_window.w = ventana

        otro = Client()
        otro.set_userid(2)
        otro.set_username("Bob")
        main_window.client_by_id[2] = otro
        main_window.colores.colores_asignados.return_value = {
            2: {"r": 10, "g": 20, "b": 30},
        }

        task = ClientTaskEstado(
            cast("EstadoTaskData", {"mensaje": "estado", "estado": "JUGANDO"})
        )
        task.run(cast("GameWindowProtocol", main_window))

        ventana.close.assert_called_once()
        ventana.deleteLater.assert_called_once()
        self.assertIsNone(main_window.w)
        main_window.update_player_list.assert_called_once_with([
            ("Bob", {"r": 10, "g": 20, "b": 30})
        ])
        main_window.update.assert_called_once()

    def test_actualizar_lista_jugadores_ignora_sin_username(self) -> None:
        """Solo entran jugadores con cliente y username conocidos."""
        main_window = _fake_main_window()
        sin_nombre = Client()
        sin_nombre.set_userid(3)
        con_nombre = Client()
        con_nombre.set_userid(4)
        con_nombre.set_username("Ana")
        main_window.client_by_id[3] = sin_nombre
        main_window.client_by_id[4] = con_nombre
        main_window.colores.colores_asignados.return_value = {
            3: {"r": 1, "g": 1, "b": 1},
            4: {"r": 2, "g": 2, "b": 2},
        }

        task = ClientTaskEstado(cast("EstadoTaskData", {"mensaje": "estado"}))
        task.actualizar_lista_jugadores(cast("GameWindowProtocol", main_window))

        main_window.update_player_list.assert_called_once_with([
            ("Ana", {"r": 2, "g": 2, "b": 2})
        ])


class TestClientTaskUserId(unittest.TestCase):
    """Asignación de user_id local y registro en `client_by_id`."""

    def test_asigna_mi_user_id_si_vacio(self) -> None:
        """El primer user_id recibido se guarda en el cliente principal."""
        main_window = _fake_main_window()
        task = ClientTaskUserId(
            cast("UserIdTaskData", {"mensaje": "user_id", "user_id": 7})
        )

        task.run(cast("GameWindowProtocol", main_window))

        self.assertEqual(main_window.client.userid(), 7)
        self.assertIn(7, main_window.client_by_id)
        main_window.update_mi_jugador_info.assert_called_once()

    def test_no_sobrescribe_user_id_existente(self) -> None:
        """Si ya hay user_id propio, solo agrega entradas a `client_by_id`."""
        main_window = _fake_main_window()
        main_window.client.set_userid(1)
        task = ClientTaskUserId(
            cast("UserIdTaskData", {"mensaje": "user_id", "user_id": 2})
        )

        task.run(cast("GameWindowProtocol", main_window))

        self.assertEqual(main_window.client.userid(), 1)
        self.assertEqual(main_window.client_by_id[2].userid(), 2)
        main_window.update_mi_jugador_info.assert_not_called()

    def test_sin_user_id_en_payload_no_hace_nada(self) -> None:
        """Payload sin `user_id` termina sin efectos."""
        main_window = _fake_main_window()
        task = ClientTaskUserId(cast("UserIdTaskData", {"mensaje": "user_id"}))

        task.run(cast("GameWindowProtocol", main_window))

        self.assertIsNone(main_window.client.userid())
        self.assertEqual(main_window.client_by_id, {})


class TestClientTaskUsername(unittest.TestCase):
    """Difusión de nombres de usuario y lista de jugadores."""

    def setUp(self) -> None:
        """Cliente local con user_id 1."""
        self.main_window = _fake_main_window()
        self.main_window.client.set_userid(1)
        self.main_window.client_by_id[1] = self.main_window.client
        peer = Client()
        peer.set_userid(2)
        self.main_window.client_by_id[2] = peer
        self.main_window.colores.colores_asignados.return_value = {
            1: {"r": 100, "g": 0, "b": 0},
            2: {"r": 0, "g": 100, "b": 0},
        }

    def test_actualiza_username_propio_y_lista(self) -> None:
        """El mensaje para mi user_id actualiza cliente y panel."""
        task = ClientTaskUsername(
            cast(
                "UsernameTaskData",
                {"mensaje": "username", "user_id": 1, "username": "Alice"},
            )
        )

        task.run(cast("GameWindowProtocol", self.main_window))

        self.assertEqual(self.main_window.client.username(), "Alice")
        self.main_window.update_player_list.assert_called_once()
        self.main_window.update_mi_jugador_info.assert_called_once()

    def test_actualiza_peer_y_refresca_colores_en_ventana_espera(self) -> None:
        """Username de otro jugador y ventana `w` recarga colores."""
        ventana = MagicMock()
        self.main_window.w = ventana
        task = ClientTaskUsername(
            cast(
                "UsernameTaskData",
                {"mensaje": "username", "user_id": 2, "username": "Bob"},
            )
        )

        task.run(cast("GameWindowProtocol", self.main_window))

        self.assertEqual(self.main_window.client_by_id[2].username(), "Bob")
        ventana.cargar_colores_asignados.assert_called_once()

    def test_payload_incompleto_no_actualiza(self) -> None:
        """Sin username o user_id no hay cambios."""
        task = ClientTaskUsername(
            cast("UsernameTaskData", {"mensaje": "username", "user_id": 1})
        )

        task.run(cast("GameWindowProtocol", self.main_window))

        self.main_window.update_player_list.assert_not_called()


class TestClientTaskActualizarListaJugadores(unittest.TestCase):
    """Lista de jugadores con orden y colores del servidor."""

    def test_construye_lista_con_username_conocido(self) -> None:
        """Usa el nombre del `client_by_id` cuando está disponible."""
        main_window = _fake_main_window()
        cliente = Client()
        cliente.set_userid(5)
        cliente.set_username("Carlos")
        main_window.client_by_id[5] = cliente

        task = ClientTaskActualizarListaJugadores(
            cast(
                "ActualizarListaJugadoresTaskData",
                {
                    "mensaje": "actualizar_lista_jugadores",
                    "jugadores": [
                        {"userid": 5, "color": {"r": 1, "g": 2, "b": 3}},
                    ],
                },
            )
        )
        task.run(cast("GameWindowProtocol", main_window))

        main_window.update_player_list.assert_called_once()
        jugadores = main_window.update_player_list.call_args[0][0]
        self.assertEqual(len(jugadores), 1)
        nombre, color = jugadores[0]
        self.assertEqual(nombre, "Carlos")
        self.assertIsInstance(color, QColor)
        self.assertEqual(color.red(), 1)

    def test_fallback_nombre_sin_cliente(self) -> None:
        """Sin cliente registrado, muestra etiqueta genérica por userid."""
        main_window = _fake_main_window()
        task = ClientTaskActualizarListaJugadores(
            cast(
                "ActualizarListaJugadoresTaskData",
                {
                    "mensaje": "actualizar_lista_jugadores",
                    "jugadores": [
                        {"userid": 9, "color": {"r": 200, "g": 200, "b": 200}},
                    ],
                },
            )
        )

        task.run(cast("GameWindowProtocol", main_window))

        nombre = main_window.update_player_list.call_args[0][0][0][0]
        self.assertIn("9", nombre)

    def test_omite_entradas_sin_userid(self) -> None:
        """Items sin `userid` no se agregan a la lista."""
        main_window = _fake_main_window()
        task = ClientTaskActualizarListaJugadores(
            cast(
                "ActualizarListaJugadoresTaskData",
                {
                    "mensaje": "actualizar_lista_jugadores",
                    "jugadores": [{"color": {"r": 1, "g": 1, "b": 1}}],
                },
            )
        )

        task.run(cast("GameWindowProtocol", main_window))

        main_window.update_player_list.assert_called_once_with([])


if __name__ == "__main__":
    unittest.main()
