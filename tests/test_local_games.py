"""Bots, guardados locales, archivos recientes y resúmenes de turnos."""

# ruff: noqa: D102, SLF001

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pyteg.client.bot_strategies import BOT_DIFFICULTIES, DEFAULT_BOT_DIFFICULTY
from pyteg.client.bots import BasicBotStrategy, choose_exchange, shortest_distance
from pyteg.client.state_model import ClientStateModel
from pyteg.persistence.archive import make_archive, write_archive
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.local import LocalGame
from pyteg.persistence.recent import RecentGames
from pyteg.persistence.turn_preview import TurnPreview
from pyteg.protocol_validation import validate_server_command
from pyteg.toml_reader import TomlReader
from tests.test_game_archives import complete_turn

_MAX_TEST_STEPS = 64


class BasicBotTests(unittest.TestCase):
    """Las decisiones no necesitan Qt, sockets ni acceso al motor."""

    def setUp(self) -> None:
        self.reader = TomlReader.from_theme("classic")
        self.strategy = BasicBotStrategy(self.reader)
        self.country = self.reader.todos_los_paises()[0]
        self.target = self.reader.adyacencias[self.country][0]
        self.model = ClientStateModel(local_userid=1)
        self.model.snapshot = {
            "estado": "JUGANDO",
            "fase": "colocacion",
            "turno": {"num_ronda": 3, "num_turno": 0, "jugador_id": 1},
            "countries": {
                name: {"userid": 2, "unidades": 2, "misiles": 0}
                for name in self.reader.todos_los_paises()
            },
        }
        self.model.snapshot["countries"][self.country]["userid"] = 1
        self.model.snapshot["countries"][self.country]["unidades"] = 8
        self.model.private_units = {"infanteria": 6}

    def test_reinforces_frontier_with_own_available_units(self) -> None:
        command = self.strategy.next_command(self.model)
        self.assertEqual(
            command,
            {
                "mensaje": "agregar_unidad",
                "pais": self.country,
                "tipo_unidad": "infanteria",
                "cantidad": 6,
            },
        )

    def test_same_and_different_card_symbols(self) -> None:
        cards = [{"pais": str(index), "simbolo": "a"} for index in range(4)]
        self.assertEqual(len(choose_exchange(cards)), 3)
        cards = [{"pais": str(index), "simbolo": str(index)} for index in range(3)]
        self.assertEqual(choose_exchange(cards), cards)
        self.assertFalse(choose_exchange(cards[:2]))

    def test_exchange_strips_private_metadata_from_command(self) -> None:
        self.model.private_cards = [
            {"pais": f"Card {index}", "simbolo": "Globo", "tipo": "pais"}
            for index in range(3)
        ]
        command = self.strategy.next_command(self.model)
        self.assertIsNotNone(command)
        if command is not None:
            self.assertEqual(command["mensaje"], "canjear_tarjetas")
            self.assertEqual(validate_server_command(command), command)
            self.assertTrue(
                all(set(card) == {"pais", "simbolo"} for card in command["tarjetas"])
            )

    def test_continent_and_wildcard_form_one_exchange(self) -> None:
        cards = [
            {
                "pais": "continente:AmericaDelSur",
                "simbolo": "Continente",
                "tipo": "continente",
                "continente": "AmericaDelSur",
            },
            {"pais": "Carta", "simbolo": "Soldado", "tipo": "pais"},
        ]
        selected = choose_exchange(
            cards, equivalences={"AmericaDelSur": ("Avion", "Tanque")}
        )
        self.assertEqual(len(selected), 2)
        self.assertEqual(
            validate_server_command({
                "mensaje": "canjear_tarjetas",
                "tarjetas": selected,
            })["tarjetas"],
            selected,
        )

    def test_super_and_full_continent_are_single_card_exchanges(self) -> None:
        for card in (
            {"pais": "Super", "simbolo": "Supertarjeta", "tipo": "especial"},
            {
                "pais": "continente:Asia",
                "simbolo": "Continente",
                "tipo": "continente",
                "continente": "Asia",
            },
        ):
            with self.subTest(card=card):
                selected = choose_exchange([card], equivalences={"Asia": ()})
                self.assertEqual(len(selected), 1)
                self.assertEqual(
                    validate_server_command({
                        "mensaje": "canjear_tarjetas",
                        "tarjetas": selected,
                    })["tarjetas"],
                    selected,
                )

    def test_early_round_does_not_attack(self) -> None:
        self.model.snapshot["fase"] = "acciones"
        self.model.snapshot["turno"]["num_ronda"] = 1
        self.assertEqual(
            self.strategy.next_command(self.model), {"mensaje": "finalizar_turno"}
        )

    def test_rejected_action_is_not_repeated_forever(self) -> None:
        self.model.snapshot["fase"] = "acciones"
        first = self.strategy.next_command(self.model)
        self.assertIsNotNone(first)
        if first is not None:
            self.strategy.acknowledge(
                first, {"accepted": False}, self.model, self.model
            )
            self.assertNotEqual(self.strategy.next_command(self.model), first)

    def test_conquest_schedules_move_and_card(self) -> None:
        self.model.snapshot["fase"] = "acciones"
        after = deepcopy(self.model)
        after.snapshot["countries"][self.target]["userid"] = 1
        after.snapshot["countries"][self.target]["unidades"] = 1
        command = {
            "mensaje": "atacar",
            "origen": self.country,
            "destino": self.target,
            "cantidad_unidades": 3,
        }
        self.strategy.next_command(self.model)
        self.strategy.acknowledge(command, {"accepted": True}, self.model, after)
        move = self.strategy.next_command(after)
        self.assertIsNotNone(move)
        if move is not None:
            self.assertEqual(move["mensaje"], "mover_unidad")
        self.assertEqual(
            self.strategy.next_command(after), {"mensaje": "reclamar_tarjeta"}
        )

    def test_shared_country_uses_own_occupants(self) -> None:
        self.model.snapshot["countries"][self.country].update({
            "userid": 2,
            "compartido": True,
            "ocupantes": [{"userid": 1, "unidades": 1}, {"userid": 2, "unidades": 10}],
        })
        self.assertEqual(self.strategy._own_units(self.model, self.country), 1)
        self.model.snapshot["fase"] = "acciones"
        self.assertEqual(
            self.strategy.next_command(self.model), {"mensaje": "finalizar_turno"}
        )

    def test_strategy_state_round_trips(self) -> None:
        self.strategy.next_command(self.model)
        self.strategy.pending.append({"mensaje": "reclamar_tarjeta"})
        restored = BasicBotStrategy(self.reader)
        restored.restore_state(self.strategy.saved_state())
        self.assertEqual(restored.saved_state(), self.strategy.saved_state())
        with self.assertRaises(ValueError):
            restored.restore_state({"turn": "bad", "actions": -1})

    def test_distance_is_public_map_only(self) -> None:
        self.assertEqual(
            shortest_distance(self.reader.adyacencias, self.country, self.target), 1
        )
        self.assertEqual(shortest_distance({}, "a", "b"), -1)


class LocalGameTests(unittest.TestCase):
    """El modo local conserva las mismas validaciones del servidor."""

    def _started(
        self,
        theme: str = "classic",
        profile: str = "classic",
        difficulty: str = DEFAULT_BOT_DIFFICULTY,
    ) -> tuple[LocalGame, ClientStateModel]:
        model = ClientStateModel(local_userid=1)

        def receive(_user: int, event: dict[str, Any]) -> None:
            model.apply_event(event)

        session = LocalGame.create(
            theme,
            "Humano",
            3,
            difficulty=difficulty,
            rules_profile=profile,
            receive=receive,
        )
        self.addCleanup(session.close)
        session.apply({
            "mensaje": "empezar",
            "segundos": 3600,
            "paises_para_victoria": 0,
        })
        session.apply({"mensaje": "empezar_partida"})
        session.sync_local()
        return session, model

    def _finish_human(self, session: LocalGame, model: ClientStateModel) -> None:
        strategy = BasicBotStrategy(TomlReader.from_theme(session.server.theme))
        for _step in range(32):
            if model.snapshot["fase"] != "colocacion":
                break
            command = strategy.next_command(model)
            self.assertIsNotNone(command)
            if command:
                result = session.apply(command)
                self.assertTrue(result and result["accepted"])
        result = session.apply({"mensaje": "finalizar_turno"})
        self.assertTrue(result and result["accepted"])

    def test_four_players_return_to_human_on_all_maps_and_profiles(self) -> None:
        for theme in ("classic", "revancha"):
            for profile in ("classic", "revancha"):
                for difficulty in BOT_DIFFICULTIES:
                    with self.subTest(
                        theme=theme, profile=profile, difficulty=difficulty
                    ):
                        session, model = self._started(theme, profile, difficulty)
                        self._finish_human(session, model)
                        steps = 0
                        while (
                            session.holder() != session.user_id
                            and steps < _MAX_TEST_STEPS
                        ):
                            self.assertTrue(session.bot_step())
                            steps += 1
                        self.assertGreater(steps, 0)
                        self.assertEqual(session.holder(), session.user_id)
                        self.assertEqual(len(session.server.dame_clientes()), 4)
                        game = session.server.game
                        self.assertIsNotNone(game)
                        if game:
                            self.assertEqual(
                                session.server.public_snapshot()["turn_order"],
                                game.lista_jugadores_orden_turno(),
                            )
                        session.close()

    def test_save_during_bot_turn_and_resume(self) -> None:
        for difficulty in BOT_DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                session, model = self._started(difficulty=difficulty)
                self._finish_human(session, model)
                self.assertTrue(session.bot_step())
                snapshot = session.server.public_snapshot()
                saved = session.draft()
                holder = session.holder()
                expected = deepcopy(session._strategies[holder]).next_command(
                    session._models[holder]
                )
                session.close()
                restored = LocalGame.open(saved)
                self.addCleanup(restored.close)
                restored.sync_local()
                self.assertEqual(restored.bot_ids, [2, 3, 4])
                self.assertEqual(restored.difficulty, difficulty)
                self.assertEqual(
                    restored.server.public_snapshot()["countries"],
                    snapshot["countries"],
                )
                self.assertEqual(
                    deepcopy(restored._strategies[holder]).next_command(
                        restored._models[holder]
                    ),
                    expected,
                )
                self.assertTrue(restored.bot_step())
                restored.close()

    def test_bot_exchanges_full_continent_through_normal_protocol(self) -> None:
        session, model = self._started("revancha", "revancha")
        self._finish_human(session, model)
        game = session.server.game
        self.assertIsNotNone(game)
        if game is None:
            return
        card = session.server.serialized(
            lambda: game.mazo().asignar_tarjeta(2, tipo="continente", continente="Asia")
        )
        self.assertIsNotNone(card)
        session.sync_player(2)
        self.assertEqual(len(session._models[2].private_cards), 1)
        self.assertTrue(session.bot_step())
        self.assertEqual(session._models[2].private_cards, [])
        self.assertEqual(game.mazo().cant_tarjetas_asignadas(2), 0)

    def test_only_own_private_events_reach_human(self) -> None:
        session, model = self._started()
        model.private_units.clear()
        self._finish_human(session, model) if model.snapshot[
            "fase"
        ] == "acciones" else None
        session.sync_player(2)
        self.assertEqual(model.local_userid, 1)
        self.assertEqual(model.private_units, {})
        self.assertEqual(session._models[2].local_userid, 2)

    def test_invalid_local_metadata_is_rejected(self) -> None:
        session, _model = self._started()
        payload = session.draft()["payload"]
        payload["local"]["bots"] = [1, 1]
        with self.assertRaises(ValueError):
            LocalGame.open(make_archive("game", payload))

    def test_single_player_and_invalid_counts(self) -> None:
        session = LocalGame.create("classic", "Solo", 0)
        self.addCleanup(session.close)
        self.assertEqual(len(session.server.dame_clientes()), 1)
        self.assertFalse(session.bot_step())
        for count in (-1, 8, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                LocalGame.create("classic", "Jugador", count)

    def test_human_name_does_not_collide_with_bots(self) -> None:
        session = LocalGame.create("classic", "Bot 1", 3)
        self.addCleanup(session.close)
        names = [player.username() for player in session.server.dame_clientes()]
        self.assertEqual(len(set(names)), 4)


class FileConvenienceTests(unittest.TestCase):
    """El índice es prescindible y la vista previa no muta una partida."""

    def test_recent_files_deduplicate_and_find_autosaves(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            recent = RecentGames(root / "autosaves")
            manual = root / "manual.pyteg"
            autosave = root / "autosaves" / "auto.pyteg"
            write_archive(manual, make_archive("game", {}))
            write_archive(autosave, make_archive("game", {}))
            recent.remember(manual)
            recent.remember(manual)
            self.assertCountEqual(
                recent.paths(), [manual.resolve(), autosave.resolve()]
            )
            manual.unlink()
            self.assertEqual(recent.paths(), [autosave.resolve()])
            recent.path.write_text("corrupt", encoding="utf-8")
            self.assertEqual(recent.paths(), [autosave.resolve()])

    def test_recent_autosave_aliases_are_one_canonical_path(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            recent = RecentGames(root / "autosaves")
            autosave = recent.directory / "auto.pyteg"
            write_archive(autosave, make_archive("game", {}))
            alias = recent.directory / ".." / "autosaves" / "auto.pyteg"
            recent.path.write_text(json.dumps([str(alias)]), encoding="utf-8")
            self.assertEqual(recent.paths(), [autosave.resolve()])

    def test_preview_contains_public_changes_and_identity(self) -> None:
        session = AsyncGame.create("classic", ["Uno", "Dos"])
        self.addCleanup(session.close)
        session.apply({"mensaje": "empezar", "paises_para_victoria": 0})
        session.apply({"mensaje": "empezar_partida"})
        before = session.server.public_snapshot()
        archive = complete_turn(session)
        preview = TurnPreview.from_archive(archive, before)
        self.assertEqual(preview.author, "Uno")
        self.assertEqual(preview.recipient, "Dos")
        self.assertTrue(preview.changes)
        self.assertNotIn("token", str(preview.snapshot))
        self.assertNotIn("private_cards", preview.snapshot)
        self.assertEqual(
            session.draft()["payload"]["checkpoint"]["history"],
            archive["payload"]["checkpoint"]["history"],
        )


if __name__ == "__main__":
    unittest.main()
