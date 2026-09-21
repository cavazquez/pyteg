"""Regresiones para reglas de turno y estado público versionado."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, cast

from pyteg.client.state_model import ClientStateModel
from pyteg.core.cartas.mazo import Mazo
from pyteg.core.partida.card_manager import CardManager
from pyteg.exceptions import InvalidActionError
from pyteg.server.juego.fase import (
    COMANDOS_POR_FASE,
    COMANDOS_SIN_FASE,
    FASE_ACCIONES,
    FASE_COLOCACION,
    FASE_POR_COMANDO,
)
from pyteg.server.juego.validators import PhaseValidator

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class _Player:
    def __init__(self, user_id: int) -> None:
        self._user_id = user_id

    def userid(self) -> int:
        return self._user_id


class _TurnManager:
    def __init__(self) -> None:
        self.round = 1
        self.turn = 0

    def num_ronda(self) -> int:
        return self.round

    def id_turno_actual(self) -> int:
        return self.turn


class _GameWithPhase:
    def __init__(self, phase: str) -> None:
        self.phase = phase

    def fase_actual(self) -> str:
        return self.phase


class TestProtocolFeatures(unittest.TestCase):
    """Verifica los contratos que protegen las nuevas transiciones."""

    def test_one_card_reward_per_turn_even_after_multiple_conquests(self) -> None:
        """Dos conquistas y dos reclamos sólo permiten una recompensa."""
        turn_manager = _TurnManager()
        cards = Mazo(["A", "B", "C"], ["Globo"])
        manager = CardManager(cards, turn_manager)
        player = cast("IClientProtocol", _Player(1))
        manager.inicializar_canjes([player.userid()])

        manager.marcar_jugador_puede_reclamar(player)
        manager.marcar_jugador_puede_reclamar(player)
        self.assertTrue(manager.puede_reclamar_tarjeta(player))
        manager.reclamar_tarjeta_jugador(player)
        self.assertFalse(manager.puede_reclamar_tarjeta(player))

        # Un reclamo repetido del mismo turno no vuelve a habilitar la tarjeta.
        manager.marcar_jugador_puede_reclamar(player)
        self.assertFalse(manager.puede_reclamar_tarjeta(player))

        turn_manager.round = 2
        manager.marcar_jugador_puede_reclamar(player)
        self.assertTrue(manager.puede_reclamar_tarjeta(player))

    def test_phase_validator_rejects_actions_before_placement_finishes(self) -> None:
        """El servidor distingue colocación de las acciones del turno."""
        game = _GameWithPhase("colocacion")
        PhaseValidator.validate_placement(game)  # type: ignore[arg-type]
        with self.assertRaises(InvalidActionError):
            PhaseValidator.validate_actions(game)  # type: ignore[arg-type]

    def test_phase_matrix_assigns_each_mutating_command_once(self) -> None:
        """La tabla central no deja comandos mutantes sin fase ni duplicados."""
        self.assertEqual(
            set(FASE_POR_COMANDO),
            {
                "agregar_unidad",
                "atacar",
                "mover_unidad",
                "finalizar_turno",
                "reclamar_tarjeta",
                "canjear_tarjetas",
                "canje_especial",
                "canjear_misil",
                "lanzar_misil",
            },
        )
        self.assertEqual(FASE_POR_COMANDO["canjear_tarjetas"], FASE_COLOCACION)
        self.assertEqual(FASE_POR_COMANDO["canjear_misil"], FASE_ACCIONES)
        self.assertEqual(COMANDOS_SIN_FASE, frozenset({"solicitar_tarjetas"}))
        self.assertEqual(
            set().union(*COMANDOS_POR_FASE.values()), set(FASE_POR_COMANDO)
        )

    def test_phase_matrix_rejects_command_without_mutating(self) -> None:
        """Un comando fuera de fase se rechaza antes de cualquier tarea."""
        placement = _GameWithPhase(FASE_COLOCACION)
        actions = _GameWithPhase(FASE_ACCIONES)

        PhaseValidator.validate_command(placement, "canjear_tarjetas")  # type: ignore[arg-type]
        PhaseValidator.validate_command(actions, "lanzar_misil")  # type: ignore[arg-type]
        with self.assertRaises(InvalidActionError):
            PhaseValidator.validate_command(placement, "lanzar_misil")  # type: ignore[arg-type]
        with self.assertRaises(InvalidActionError):
            PhaseValidator.validate_command(actions, "canje_especial")  # type: ignore[arg-type]

    def test_state_model_applies_revision_zero_and_reports_gaps(self) -> None:
        """El primer snapshot puede ser cero y los huecos piden resincronización."""
        model = ClientStateModel()
        snapshot: dict[str, Any] = {
            "mensaje": "snapshot",
            "revision": 0,
            "estado": "Inicial",
            "theme": "classic",
            "map_hash": "hash",
            "players": [],
            "countries": {},
        }
        self.assertTrue(model.apply_event(snapshot).applied)
        self.assertEqual(model.revision, 0)
        self.assertTrue(model.apply_event({**snapshot, "revision": 2}).gap)
        self.assertTrue(model.needs_snapshot())
