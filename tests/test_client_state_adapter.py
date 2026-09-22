"""Pruebas de la fuente única de estado para clientes headless y Qt."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any

from pyteg.client.event_processor import ClientEventProcessor
from pyteg.client.state_adapter import QtClientStateAdapter
from pyteg.client.state_model import ClientStateModel

if TYPE_CHECKING:
    from PySide6.QtGui import QColor


class _WindowDouble:
    """Superficie mínima que consume el adaptador Qt sin abrir una ventana."""

    def __init__(self) -> None:
        """Inicializa los valores que el adaptador proyecta."""
        self.scene = None
        self.fase_actual: str | None = None
        self.unidades_pendientes_servidor = 0
        self.partida_finalizada = False
        self.client_public_revision = -1
        self.game_states: list[str] = []
        self.players: list[tuple[str, QColor]] = []
        self.player_statuses: list[Any] = []
        self.turns: list[tuple[int, int, int | None]] = []

    def update_game_state(self, state: str) -> None:
        """Registra el estado público proyectado."""
        self.game_states.append(state)

    def set_configuracion_partida(
        self,
        _seconds: int,
        _victory: int,
        *,
        objetivos_secretos: bool,
        misiles_habilitados: bool,
    ) -> None:
        """Acepta la configuración pública para el doble."""
        _ = objetivos_secretos, misiles_habilitados

    def update_player_list(self, players: list[tuple[str, QColor]]) -> None:
        """Registra la lista pública proyectada."""
        self.players = players

    def update_player_statuses(self, statuses: list[Any]) -> None:
        """Registra estados públicos de los jugadores."""
        self.player_statuses = statuses

    def update_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_id: int | None,
        _nombre: str | None,
        _color: str | None,
    ) -> None:
        """Registra el turno público proyectado."""
        self.turns.append((num_turno, num_ronda, jugador_id))

    def refresh_gameplay_actions(self) -> None:
        """El doble no tiene toolbar que refrescar."""


def _snapshot(revision: int, *, resync: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "mensaje": "snapshot",
        "snapshot_version": 1,
        "revision": revision,
        "estado": "JUGANDO",
        "theme": "test",
        "map_hash": "hash",
        "configuracion": {
            "segundos_por_turno": 20,
            "paises_para_victoria": 2,
            "objetivos_secretos": False,
            "misiles_habilitados": True,
        },
        "players": [
            {
                "userid": 1,
                "username": "Bot 1",
                "color": {"r": 255, "g": 0, "b": 0},
                "admin": True,
                "connected": True,
                "eliminated": False,
            }
        ],
        "countries": {
            "A": {"userid": 1, "unidades": 3, "misiles": 2},
        },
        "fase": "acciones",
        "turno": {"num_turno": 4, "num_ronda": 2, "jugador_id": 1},
        "refuerzos_pendientes": 0,
    }
    if resync:
        payload["resync"] = True
    return payload


class TestClientStateAdapter(unittest.TestCase):
    """El modelo headless y el adaptador Qt consumen exactamente la misma traza."""

    def test_headless_and_qt_projection_converge_after_resync(self) -> None:
        """Un hueco se recupera sin ejecutar un command_result como acción."""
        trace = [
            _snapshot(0),
            _snapshot(2),
            _snapshot(2, resync=True),
            {
                "mensaje": "command_result",
                "command_id": "cmd-1",
                "accepted": True,
                "revision": 2,
            },
        ]
        headless = ClientStateModel()
        qt_model = ClientStateModel()
        processor = ClientEventProcessor(headless)
        qt_processor = ClientEventProcessor(qt_model)
        window = _WindowDouble()
        adapter = QtClientStateAdapter(window, qt_model)  # type: ignore[arg-type]

        for event in trace:
            processor.process(event)
            result = qt_processor.process(event)
            adapter.apply(event, result)

        self.assertEqual(headless.revision, qt_model.revision)
        self.assertEqual(headless.snapshot, qt_model.snapshot)
        self.assertFalse(headless.needs_snapshot())
        self.assertFalse(qt_model.needs_snapshot())
        self.assertEqual(qt_model.command_results["cmd-1"]["accepted"], True)
        self.assertEqual(window.client_public_revision, 2)
        self.assertEqual(window.game_states[-1], "JUGANDO")
        self.assertEqual(window.fase_actual, "acciones")
        self.assertEqual(window.turns[-1], (4, 2, 1))
        self.assertEqual(window.players[0][0], "Bot 1")
        self.assertTrue(window.player_statuses[0].admin)
