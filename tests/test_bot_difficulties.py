"""Niveles distintos con las mismas reglas, estado privado y protocolo."""

# ruff: noqa: D102, SLF001

from __future__ import annotations

import unittest
from copy import deepcopy
from typing import Any, cast

from pyteg.client.bot_planning import BotObjective, estimate_conquest
from pyteg.client.bot_strategies import (
    BOT_DIFFICULTIES,
    BotStrategyFactory,
    EasyBotStrategy,
    HardBotStrategy,
    NormalBotStrategy,
)
from pyteg.client.bots import BasicBotStrategy, BotAttack, frontier_distances
from pyteg.client.state_model import ClientStateModel
from pyteg.core.partida.pactos import NoPactManager
from pyteg.persistence.archive import make_archive
from pyteg.persistence.local import LocalGame
from pyteg.protocol_validation import (
    MessageValidationError,
    validate_client_event,
    validate_server_command,
)
from pyteg.toml_reader import TomlReader


class BotDifficultyTests(unittest.TestCase):
    """Usa proyecciones de cliente y fronteras públicas controladas."""

    def setUp(self) -> None:
        self.reader = TomlReader.from_theme("classic")
        south = list(self.reader.get_paises("Sudamerica"))
        asia = list(self.reader.get_paises("Asia"))
        self.origin, self.other = south[:2]
        self.target, self.next_target = asia[:2]
        self.reader.adyacencias = {name: [] for name in self.reader.todos_los_paises()}
        self.model = ClientStateModel(local_userid=1)
        self.model.snapshot = {
            "estado": "JUGANDO",
            "fase": "acciones",
            "turno": {"num_ronda": 3, "num_turno": 0, "jugador_id": 1},
            "turn_order": [1, 3, 2],
            "countries": {
                name: {"userid": 3, "unidades": 2, "misiles": 0}
                for name in self.reader.todos_los_paises()
            },
            "players": [
                {"userid": 1, "color": {"r": 0, "g": 0, "b": 255}},
                {"userid": 2, "color": {"r": 255, "g": 0, "b": 0}},
                {"userid": 3, "color": {"r": 0, "g": 255, "b": 0}},
            ],
        }
        self.model.private_units = {"infanteria": 6}
        self._country(self.origin, 1, 12)
        self._country(self.other, 2, 2)
        self._country(self.target, 2, 2)
        self._edge(self.origin, self.other)
        self._edge(self.origin, self.target)

    def _country(self, name: str, owner: int, units: int) -> None:
        self.model.snapshot["countries"][name].update({
            "userid": owner,
            "unidades": units,
        })

    def _edge(self, first: str, second: str) -> None:
        self.reader.adyacencias[first].append(second)
        self.reader.adyacencias[second].append(first)

    def test_factory_builds_three_different_strategies_and_accepts_legacy(self) -> None:
        factory = BotStrategyFactory()
        expected = (EasyBotStrategy, NormalBotStrategy, HardBotStrategy)
        for difficulty, implementation in zip(BOT_DIFFICULTIES, expected, strict=True):
            with self.subTest(difficulty=difficulty):
                self.assertIsInstance(
                    factory.create(difficulty, self.reader), implementation
                )
        self.assertIsInstance(factory.create("basic", self.reader), NormalBotStrategy)
        invalid_levels: tuple[object, ...] = ("", "unknown", None, [], True)
        for invalid in invalid_levels:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                factory.create(cast("str", invalid), self.reader)

    def test_easy_resuming_preserves_next_varied_choice(self) -> None:
        first = EasyBotStrategy(self.reader)
        first.next_command(self.model)
        restored = EasyBotStrategy(self.reader)
        restored.restore_state(deepcopy(first.saved_state()))
        self.assertEqual(
            first.next_command(self.model), restored.next_command(self.model)
        )

    def test_rejected_placement_is_not_retried_by_any_level(self) -> None:
        self.model.snapshot["fase"] = "colocacion"
        for difficulty in BOT_DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                strategy = BotStrategyFactory().create(difficulty, self.reader)
                command = strategy.next_command(self.model)
                self.assertIsNotNone(command)
                if command is not None:
                    strategy.acknowledge(
                        command, {"accepted": False}, self.model, self.model
                    )
                    self.assertNotEqual(strategy.next_command(self.model), command)

    def test_all_levels_emit_protocol_commands_without_mutating_projection(
        self,
    ) -> None:
        for difficulty in BOT_DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                before = deepcopy(self.model)
                command = (
                    BotStrategyFactory()
                    .create(difficulty, self.reader)
                    .next_command(self.model)
                )
                self.assertIsNotNone(command)
                if command is not None:
                    self.assertEqual(validate_server_command(command), command)
                self.assertEqual(self.model, before)

    def test_normal_reinforces_weak_frontier_in_chunks(self) -> None:
        self.model.snapshot["fase"] = "colocacion"
        self._country(self.other, 1, 2)
        self._country(self.target, 2, 5)
        self._edge(self.other, self.target)
        command = NormalBotStrategy(self.reader).next_command(self.model)
        self.assertIsNotNone(command)
        if command is not None:
            self.assertEqual(command["pais"], self.other)
            self.assertEqual(command["cantidad"], 5)

    def test_interior_armies_move_towards_frontier_without_crossing_enemies(
        self,
    ) -> None:
        self.reader.adyacencias = {name: [] for name in self.reader.todos_los_paises()}
        self._country(self.other, 1, 1)
        self._edge(self.origin, self.other)
        self._edge(self.other, self.target)
        distances = frontier_distances(
            self.reader.adyacencias, {self.origin, self.other}
        )
        self.assertEqual(distances, {self.other: 0, self.origin: 1})
        for difficulty in BOT_DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                command = (
                    BotStrategyFactory()
                    .create(difficulty, self.reader)
                    .next_command(self.model)
                )
                self.assertEqual(
                    command,
                    {
                        "mensaje": "mover_unidad",
                        "origen": self.origin,
                        "destino": self.other,
                        "cantidad": 11,
                    },
                )
                if command is not None:
                    self.assertEqual(validate_server_command(command), command)

    def test_reposition_keeps_objective_garrison_and_rejected_moves_are_skipped(
        self,
    ) -> None:
        self.reader.adyacencias = {name: [] for name in self.reader.todos_los_paises()}
        self._country(self.other, 1, 1)
        self._edge(self.origin, self.other)
        self._edge(self.other, self.target)
        self.model.private_objective = {
            "objetivo_id": "conquistar_18_paises_dos_tropas",
            "descripcion": "",
        }
        strategy = HardBotStrategy(self.reader)
        command = strategy.next_command(self.model)
        if command is not None:
            self.assertEqual(command["cantidad"], 10)
            strategy.acknowledge(command, {"accepted": False}, self.model, self.model)
            self.assertEqual(
                strategy.next_command(self.model), {"mensaje": "finalizar_turno"}
            )

    def test_normal_leaves_defense_after_conquest(self) -> None:
        self._country(self.origin, 1, 8)
        self._country(self.other, 2, 8)
        self._country(self.target, 1, 1)
        self._edge(self.target, self.next_target)
        normal = NormalBotStrategy(self.reader)
        self.assertEqual(normal._conquest_move(self.model, self.origin, self.target), 4)
        self.assertEqual(
            BasicBotStrategy(self.reader)._conquest_move(
                self.model, self.origin, self.target
            ),
            7,
        )

    def test_hard_prioritizes_its_own_continent_objective(self) -> None:
        strategy = HardBotStrategy(self.reader)
        self.model.private_objective = {
            "objetivo_id": "conquistar_asia_africa",
            "descripcion": "",
        }
        command = strategy.next_command(self.model)
        self.assertIsNotNone(command)
        if command is not None:
            self.assertEqual(command["destino"], self.target)

    def test_hard_rejects_low_probability_attack(self) -> None:
        self._country(self.origin, 1, 3)
        self._country(self.other, 2, 8)
        self._country(self.target, 2, 3)
        self.assertEqual(
            HardBotStrategy(self.reader).next_command(self.model),
            {"mensaje": "finalizar_turno"},
        )

    def test_hard_evaluates_a_following_conquest(self) -> None:
        self._edge(self.target, self.next_target)
        strategy = HardBotStrategy(self.reader)
        path = BotAttack(self.origin, self.target, 12, 2, 3)
        dead_end = BotAttack(self.origin, self.other, 12, 2, 3)
        self.assertGreater(strategy._next_conquest_value(self.model, path, 8), 0)
        self.assertEqual(strategy._next_conquest_value(self.model, dead_end, 8), 0)
        self.assertEqual(strategy._next_conquest_value(self.model, path, 1), 0)

    def test_hard_preserves_objective_minimum_garrisons(self) -> None:
        self.model.private_objective = {
            "objetivo_id": "conquistar_18_paises_dos_tropas",
            "descripcion": "",
        }
        self._country(self.target, 1, 1)
        strategy = HardBotStrategy(self.reader)
        amount = strategy._conquest_move(self.model, self.origin, self.target)
        self.assertGreaterEqual(amount, 1)
        self.assertGreaterEqual(12 - amount, 2)
        self.model.snapshot["fase"] = "colocacion"
        self.reader.adyacencias = {name: [] for name in self.reader.todos_los_paises()}
        command = strategy.next_command(self.model)
        if command is not None:
            self.assertEqual(command["pais"], self.target)
            self.assertEqual(command["cantidad"], 1)

    def test_estimate_uses_defender_ties_and_public_dice_limits(self) -> None:
        chance = estimate_conquest(self.model, 1, 1)
        self.assertAlmostEqual(chance.probability, 15 / 36)
        self.assertAlmostEqual(chance.survivors, 1)
        self.model.rules = {"attack_dice_max": 1, "defense_dice_max": 3}
        cautious = estimate_conquest(self.model, 5, 3)
        self.model.rules["attack_dice_max"] = 3
        self.assertLess(
            cautious.probability, estimate_conquest(self.model, 5, 3).probability
        )

    def test_estimate_obeys_snow_and_tailwind(self) -> None:
        normal = estimate_conquest(self.model, 5, 3).probability
        self.model.snapshot["situacion"] = {"efecto": "snow"}
        snow = estimate_conquest(self.model, 5, 3).probability
        self.model.snapshot["situacion"] = {"efecto": "tailwind"}
        wind = estimate_conquest(self.model, 5, 3).probability
        self.assertLess(snow, normal)
        self.assertGreater(wind, normal)

    def test_large_armies_are_bounded_and_empty_assault_is_safe(self) -> None:
        for units, defenders in ((1000, 900), (1, 1000), (0, 2), (5, 0)):
            with self.subTest(units=units, defenders=defenders):
                estimate = estimate_conquest(self.model, units, defenders)
                self.assertGreaterEqual(estimate.probability, 0)
                self.assertLessEqual(estimate.probability, 1)
                self.assertGreaterEqual(estimate.survivors, 0)
                self.assertLessEqual(estimate.survivors, units)

    def test_destroy_objective_uses_public_color_and_live_turn_order(self) -> None:
        goal = {"color_objetivo": "rojo", "jugador_alternativo": "derecha"}
        self.assertEqual(BotObjective._target_player(goal, self.model), 2)
        goal["color_objetivo"] = "blanco"
        self.assertEqual(BotObjective._target_player(goal, self.model), 3)
        self.model.snapshot["turn_order"] = [1, 2, 3]
        self.assertEqual(BotObjective._target_player(goal, self.model), 2)
        goal["jugador_alternativo"] = "izquierda"
        self.assertEqual(BotObjective._target_player(goal, self.model), 3)
        self.model.snapshot.pop("turn_order")
        self.assertIsNone(BotObjective._target_player(goal, self.model))

    def test_revancha_supports_paired_objectives_and_islands(self) -> None:
        reader = TomlReader.from_theme("revancha")
        model = ClientStateModel(local_userid=1)
        model.snapshot = {
            "countries": {
                name: {"userid": 2, "unidades": 2} for name in reader.todos_los_paises()
            }
        }
        model.private_objective = {
            "objetivo_id": "ocupar_europa_america_del_sur+ocupar_asia_america_central",
            "descripcion": "",
        }
        goal = BotObjective.from_model(reader, model)
        self.assertEqual(len(goal.goals), 2)
        for continent in ("Europa", "Asia", "AmericaDelSur", "AmericaCentral"):
            self.assertGreater(
                goal.country_value(model, next(iter(reader.get_paises(continent)))), 0
            )
        model.private_objective["objetivo_id"] = "ocupar_africa_europa_asia_islas"
        goal = BotObjective.from_model(reader, model)
        self.assertGreater(
            goal.country_value(model, "Tonga"), goal.country_value(model, "NuevaGuinea")
        )

    def test_destroy_objective_falls_back_to_countries_when_color_is_absent(
        self,
    ) -> None:
        self.model.private_objective = {
            "objetivo_id": "destruir_violeta",
            "descripcion": "",
        }
        objective = BotObjective.from_model(self.reader, self.model)
        self.assertGreater(objective.country_value(self.model, self.target), 0)
        self.model.private_objective["objetivo_id"] = "destruir_azul"
        own_color = BotObjective.from_model(self.reader, self.model)
        self.assertGreater(own_color.country_value(self.model, self.target), 0)


class LocalDifficultyPersistenceTests(unittest.TestCase):
    """La elección de nivel y las decisiones se conservan al reabrir."""

    def test_levels_save_and_restore_their_strategies_on_both_maps(self) -> None:
        for theme in ("classic", "revancha"):
            for difficulty in BOT_DIFFICULTIES:
                with self.subTest(theme=theme, difficulty=difficulty):
                    session = LocalGame.create(
                        theme, "Humano", 3, difficulty=difficulty
                    )
                    try:
                        saved = session.draft()
                    finally:
                        session.close()
                    restored = LocalGame.open(saved)
                    try:
                        self.assertEqual(restored.difficulty, difficulty)
                        self.assertEqual(
                            restored.draft()["payload"]["local"]["difficulty"],
                            difficulty,
                        )
                        expected = type(
                            BotStrategyFactory().create(
                                difficulty, TomlReader.from_theme(theme)
                            )
                        )
                        self.assertTrue(
                            all(
                                isinstance(strategy, expected)
                                for strategy in restored._strategies.values()
                            )
                        )
                    finally:
                        restored.close()

    def test_blockades_follow_rule_profile_independently_of_map(self) -> None:
        for theme in ("classic", "revancha"):
            for profile in ("classic", "revancha"):
                with self.subTest(theme=theme, profile=profile):
                    session = LocalGame.create(
                        theme, "Humano", 3, rules_profile=profile
                    )
                    try:
                        session.apply({"mensaje": "empezar", "paises_para_victoria": 0})
                        session.apply({"mensaje": "empezar_partida"})
                        game = session.server.game
                        self.assertIsNotNone(game)
                        if game is not None:
                            self.assertEqual(
                                isinstance(game.pactos(), NoPactManager),
                                profile == "classic",
                            )
                    finally:
                        session.close()

    def test_snapshot_turn_order_is_optional_and_validated(self) -> None:
        session = LocalGame.create("classic", "Humano", 3)
        try:
            snapshot = {"mensaje": "snapshot", **session.server.public_snapshot()}
            snapshot.pop("turn_order")
            self.assertEqual(validate_client_event(snapshot), snapshot)
            snapshot["turn_order"] = [1, 3, 2]
            self.assertEqual(validate_client_event(snapshot), snapshot)
            invalid_orders: tuple[object, ...] = (None, "1,2", [True], [-1], [1, 1])
            for order in invalid_orders:
                with (
                    self.subTest(order=order),
                    self.assertRaises(MessageValidationError),
                ):
                    validate_client_event({**snapshot, "turn_order": order})
        finally:
            session.close()

    def test_legacy_basic_and_missing_difficulty_remain_readable(self) -> None:
        session = LocalGame.create("classic", "Humano", 3)
        try:
            payload = session.draft()["payload"]
        finally:
            session.close()
        for legacy in ("basic", None):
            with self.subTest(legacy=legacy):
                copy = deepcopy(payload)
                if legacy is None:
                    copy["local"].pop("difficulty")
                else:
                    copy["local"]["difficulty"] = legacy
                restored = LocalGame.open(make_archive("game", copy))
                try:
                    self.assertEqual(restored.difficulty, "normal")
                finally:
                    restored.close()

    def test_invalid_difficulty_is_rejected_for_creation_and_saved_files(self) -> None:
        session = LocalGame.create("classic", "Humano", 3)
        try:
            payload = session.draft()["payload"]
        finally:
            session.close()
        invalid_levels: tuple[object, ...] = ("unknown", True, [], {})
        for invalid in invalid_levels:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    LocalGame.create(
                        "classic", "Humano", 3, difficulty=cast("str", invalid)
                    )
                copy: dict[str, Any] = deepcopy(payload)
                copy["local"]["difficulty"] = invalid
                with self.assertRaises(ValueError):
                    LocalGame.open(make_archive("game", copy))
