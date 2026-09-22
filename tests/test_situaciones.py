"""Pruebas de las cartas de situación y su integración con cualquier mapa."""

from __future__ import annotations

import random
import unittest
from typing import TYPE_CHECKING, cast

from pyteg.core.partida.turn_manager import TurnManager
from pyteg.core.situaciones.catalog import build_situation_deck, create_effect
from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.model import SituationCard, SituationContext
from pyteg.core.situaciones.runtime import SituationRuntime
from pyteg.exceptions import InvalidActionError
from pyteg.server.juego.mapa import Mapa

if TYPE_CHECKING:
    from pyteg.protocols.mapa import IMapProtocol


class _Map:
    def __init__(self) -> None:
        self._owners = {"A": 1, "B": 1, "C": 2, "D": 2}
        self._continents = {"A": "left", "B": "left", "C": "right", "D": "right"}

    def paises(self) -> list[str]:
        return list(self._owners)

    def ocupado_por(self, country: str) -> int | None:
        return self._owners[country]

    def continente(self, country: str) -> str:
        return self._continents[country]


class _Dice:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)

    def roll(self) -> int:
        return next(self.values)


class SituationTests(unittest.TestCase):
    """Verifica estrategias, Null Object y ciclo de una carta por ronda."""

    def setUp(self) -> None:
        """Crea un mapa mínimo con dos continentes."""
        self.mapa = cast("IMapProtocol", _Map())

    def test_revancha_deck_has_fifty_cards(self) -> None:
        """El mazo oficial contiene cincuenta cartas."""
        deck = build_situation_deck("revancha", rng=random.Random(7))  # noqa: S311
        self.assertEqual(deck.total(), 50)

    def test_null_object_keeps_base_rules(self) -> None:
        """El objeto nulo no altera combate, acciones ni refuerzos."""
        runtime = SituationRuntime.none(self.mapa)
        self.assertEqual(runtime.attack_dice(3), 3)
        self.assertEqual(runtime.defense_dice(3), 3)
        self.assertEqual(runtime.extra_reinforcements(1), 0)
        self.assertTrue(runtime.can_claim_country_card(1))
        runtime.validate_attack("A", "B")
        runtime.validate_action(1, "atacar", "#ff0000")

    def test_effects_are_map_agnostic(self) -> None:
        """Los efectos de dados y refuerzos no usan nombres fijos de países."""
        context = SituationContext(self.mapa, 2, (1, 2), {1: "#ff0000", 2: "#00ff00"})
        self.assertEqual(
            create_effect(SituationCard("snow", "Nieve", "snow")).defense_dice(
                3, context
            ),
            4,
        )
        self.assertEqual(
            create_effect(SituationCard("tailwind", "Viento", "tailwind")).attack_dice(
                3, context
            ),
            4,
        )
        self.assertEqual(
            create_effect(
                SituationCard("extras", "Extras", "extra_reinforcements")
            ).extra_reinforcements(1, context),
            1,
        )

    def test_open_and_closed_borders_validate_continent_relation(self) -> None:
        """Las fronteras consultan los continentes provistos por el mapa."""
        context = SituationContext(self.mapa, 2, (1, 2), {})
        open_effect = create_effect(SituationCard("open", "Abiertas", "open_borders"))
        closed_effect = create_effect(
            SituationCard("closed", "Cerradas", "closed_borders")
        )
        open_effect.validate_attack("A", "C", context)
        closed_effect.validate_attack("A", "B", context)
        with self.assertRaises(InvalidActionError):
            open_effect.validate_attack("A", "B", context)
        with self.assertRaises(InvalidActionError):
            closed_effect.validate_attack("A", "C", context)

    def test_rest_card_is_skipped_when_color_is_absent(self) -> None:
        """Descanso se reemplaza si su color no participa."""
        deck = SituationDeck(
            [SituationCard("rest", "Descanso", "rest", "#ff0000")],
            rng=random.Random(1),  # noqa: S311
        )
        runtime = SituationRuntime(self.mapa, deck, dice_source=_Dice([1, 1]))
        card = runtime.begin_round(2, (1, 2), {1: "#00ff00", 2: "#0000ff"})
        self.assertEqual(card.card_id, "none")

    def test_crisis_blocks_all_players_tied_at_lowest_roll(self) -> None:
        """Crisis bloquea a todos los jugadores empatados en el mínimo."""
        deck = SituationDeck(
            [SituationCard("crisis", "Crisis", "crisis")],
            rng=random.Random(1),  # noqa: S311
        )
        runtime = SituationRuntime(self.mapa, deck, dice_source=_Dice([2, 2, 5]))
        runtime.begin_round(2, (1, 2, 3), {})
        self.assertFalse(runtime.can_claim_country_card(1))
        self.assertFalse(runtime.can_claim_country_card(2))

    def test_round_start_is_idempotent(self) -> None:
        """Reintentar una ronda no roba una segunda carta."""
        deck = SituationDeck(
            [SituationCard("snow", "Nieve", "snow")],
            rng=random.Random(1),  # noqa: S311
        )
        runtime = SituationRuntime(self.mapa, deck)
        first = runtime.begin_round(2, (1, 2), {})
        second = runtime.begin_round(2, (1, 2), {})
        self.assertEqual(first, second)
        self.assertEqual(deck.discarded(), 1)

    def test_seeded_crisis_dice_are_reproducible(self) -> None:
        """La fuente inyectada hace reproducibles los resultados de Crisis."""
        cards = [SituationCard("crisis", "Crisis", "crisis")]
        first = SituationRuntime(
            self.mapa,
            SituationDeck(cards, rng=random.Random(3)),  # noqa: S311
            dice_rng=random.Random(3),  # noqa: S311
        )
        second = SituationRuntime(
            self.mapa,
            SituationDeck(cards, rng=random.Random(3)),  # noqa: S311
            dice_rng=random.Random(3),  # noqa: S311
        )
        first.begin_round(2, (1, 2), {})
        second.begin_round(2, (1, 2), {})
        self.assertEqual(first.crisis_rolls(), second.crisis_rolls())

    def test_extra_reinforcement_waits_for_the_revealed_round_card(self) -> None:
        """El bonus se consulta después de revelar la carta de la ronda."""
        mapa = Mapa(
            lambda: {
                "A": [1, "America", 1],
                "B": [1, "America", 1],
                "C": [1, "America", 2],
            }
        )
        runtime = SituationRuntime(
            mapa,
            SituationDeck(
                [SituationCard("extras", "Refuerzos extras", "extra_reinforcements")],
                rng=random.Random(4),  # noqa: S311
            ),
        )
        turn_manager = TurnManager(mapa, runtime)
        turn_manager.inicializar_turnos([1, 2])
        turn_manager.iniciar_nueva_ronda([1, 2], es_segundo_turno=True)
        runtime.begin_round(2, (1, 2), {})
        self.assertEqual(turn_manager.turno_actual().cant_unidades(), 4)


if __name__ == "__main__":
    unittest.main()
