"""Tests de sincronización de sesión servidor-cliente."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from pyteg.server.juego.session_sync import (
    actualizar_lista_jugadores_ui,
    clientes_ordenados_por_turno,
    clientes_por_id,
    enviar_unidades_disponibles,
)

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.game import Game


class _FakeClient:
    def __init__(self, user_id: int, name: str) -> None:
        self._user_id = user_id
        self._name = name
        self.transmisor = MagicMock()
        self._color = MagicMock()

    def userid(self) -> int:
        return self._user_id

    def username(self) -> str:
        return self._name

    def color_actual(self) -> MagicMock:
        return self._color


class _FakeTurno:
    def __init__(self, jugador_id: int, unidades: dict[str, int]) -> None:
        self._jugador_id = jugador_id
        self._unidades = unidades

    def jugador_actual(self) -> int:
        return self._jugador_id

    def unidades_por_tipo(self) -> dict[str, int]:
        return self._unidades


class _FakeGame:
    def __init__(self, orden: list[int], turno: _FakeTurno) -> None:
        self._orden = orden
        self._turno = turno

    def lista_jugadores_orden_turno(self) -> list[int]:
        return self._orden

    def turno_actual(self) -> _FakeTurno:
        return self._turno


class TestSessionSync(unittest.TestCase):
    """Helpers compartidos entre Server y Coordinator."""

    def test_clientes_ordenados_por_turno(self) -> None:
        """Respeta el orden de turno y agrega clientes extra al final."""
        c1 = _FakeClient(1, "A")
        c2 = _FakeClient(2, "B")
        c3 = _FakeClient(3, "C")
        game = _FakeGame([2, 1], _FakeTurno(2, {"infanteria": 3}))

        ordenados = clientes_ordenados_por_turno(
            cast("Game", game),
            [cast("Client", c) for c in (c1, c3, c2)],
        )

        self.assertEqual([c.userid() for c in ordenados], [2, 1, 3])

    def test_enviar_unidades_disponibles_al_jugador_en_turno(self) -> None:
        """Solo el jugador activo recibe el panel de unidades."""
        jugador_id = 5
        jugador = _FakeClient(jugador_id, "Turno")
        otro = _FakeClient(9, "Otro")
        unidades = {"infanteria": 4, "Africa": 2}
        game = _FakeGame([jugador_id], _FakeTurno(jugador_id, unidades))

        def obtener(uid: int) -> Client | None:
            return cast("Client", jugador) if uid == jugador_id else None

        enviar_unidades_disponibles(cast("Game", game), obtener)

        jugador.transmisor.enviar_unidades_disponibles.assert_called_once_with(unidades)
        otro.transmisor.enviar_unidades_disponibles.assert_not_called()

    def test_actualizar_lista_jugadores_ui(self) -> None:
        """Propaga userid y color en orden de turno a cada cliente."""
        c1 = _FakeClient(1, "A")
        c2 = _FakeClient(2, "B")
        game = _FakeGame([2, 1], _FakeTurno(2, {"infanteria": 1}))

        def get_clients() -> list[Client]:
            return [cast("Client", c1), cast("Client", c2)]

        actualizar_lista_jugadores_ui(cast("Game", game), get_clients)

        c1.transmisor.actualizar_lista_jugadores.assert_called_once()
        payload = c1.transmisor.actualizar_lista_jugadores.call_args[0][0]
        self.assertEqual(payload[0][0], 2)
        self.assertEqual(payload[1][0], 1)

    def test_clientes_por_id(self) -> None:
        """Construye el índice userid -> cliente."""
        c1 = _FakeClient(10, "X")
        self.assertIs(clientes_por_id([cast("Client", c1)])[10], c1)


if __name__ == "__main__":
    unittest.main()
