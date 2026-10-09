"""Guardados atómicos, historial público y turnos portables sin red."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from pyteg.core.turnos.unit_pool import unidades_disponibles_en_pais
from pyteg.persistence.archive import (
    FileRepository,
    MemoryRepository,
    make_archive,
    read_archive,
    write_archive,
)
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.history import Replay


def complete_turn(session: AsyncGame) -> dict[str, Any]:
    """Coloca todos los refuerzos disponibles y sella el turno local.

    Returns:
        Archivo listo para el siguiente jugador.

    Raises:
        RuntimeError: Si el fixture no inició la partida.

    """
    game = session.server.game
    if game is None:
        msg = "La partida de prueba no comenzó"
        raise RuntimeError(msg)
    snapshot = session.server.public_snapshot()
    for country, data in snapshot["countries"].items():
        if data["userid"] != session.user_id:
            continue
        available = unidades_disponibles_en_pais(
            game.turno_actual(), session.server.mapa.continente(country)
        )
        if available and game.fase_actual() == "colocacion":
            session.apply({
                "mensaje": "agregar_unidad",
                "pais": country,
                "tipo_unidad": "infanteria",
                "cantidad": available,
            })
    session.apply({"mensaje": "finalizar_turno"})
    return session.export_turn()


class ArchiveTests(unittest.TestCase):
    """Los archivos se validan antes de usarlos y nunca quedan truncados."""

    def test_round_trip_all_formats(self) -> None:
        """Los tres formatos conservan datos Unicode y versión."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "partida.pyteg"
            for kind in ("game", "turn", "replay"):
                document = make_archive(
                    kind, {"nombre": "País, misil y acción", "datos": [1, None]}
                )
                write_archive(path, document)
                self.assertEqual(read_archive(path, kind=kind), document)

    def test_damage_and_wrong_version_are_rejected(self) -> None:
        """Cambiar un dato sin su integridad impide abrir la copia."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "partida.pyteg"
            document = make_archive("game", {"dato": 1})
            document["payload"]["dato"] = 2
            path.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                read_archive(path)
            document["version"] = 999
            path.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                read_archive(path)

    def test_failed_write_preserves_previous_file(self) -> None:
        """Un fallo antes del reemplazo conserva el guardado válido anterior."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "partida.pyteg"
            original = make_archive("game", {"dato": 1})
            write_archive(path, original)
            with (
                patch(
                    "pyteg.persistence.archive.os.fsync",
                    side_effect=OSError("disco lleno"),
                ),
                self.assertRaises(OSError),
            ):
                write_archive(path, make_archive("game", {"dato": 2}))
            self.assertEqual(read_archive(path), original)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_windows_flushes_file_without_opening_directory(self) -> None:
        """El guardado Windows sincroniza el archivo y evita flags POSIX."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "partida.pyteg"
            document = make_archive("game", {"dato": 1})
            with (
                patch("pyteg.persistence.archive.sys.platform", "win32"),
                patch("pyteg.persistence.archive.os.fsync") as flush,
            ):
                write_archive(path, document)
            flush.assert_called_once()
            self.assertEqual(read_archive(path), document)

    def test_size_and_json_limits(self) -> None:
        """Las copias grandes, profundas o no JSON se rechazan."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "partida.pyteg"
            path.write_text("not json")
            with self.assertRaises(ValueError):
                read_archive(path)
            path.write_bytes(b" " * 33)
            with (
                patch("pyteg.persistence.archive.MAX_ARCHIVE_BYTES", 32),
                self.assertRaises(ValueError),
            ):
                read_archive(path)
            value: Any = 1
            for _level in range(70):
                value = [value]
            with self.assertRaises(ValueError):
                write_archive(path, make_archive("game", {"deep": value}))

    def test_repository_strategies_do_not_share_mutable_data(self) -> None:
        """Memoria y archivo exponen el mismo contrato independiente."""
        with TemporaryDirectory() as directory:
            for repository in (
                MemoryRepository(),
                FileRepository(Path(directory) / "autosave.pyteg"),
            ):
                self.assertIsNone(repository.load())
                document = make_archive("game", {"dato": 1})
                repository.save(document)
                document["payload"]["dato"] = 2
                restored = repository.load()
                self.assertIsNotNone(restored)
                if restored:
                    self.assertEqual(restored["payload"]["dato"], 1)


class AsyncGameTests(unittest.TestCase):
    """Las reglas de TCP se usan sin sockets ni vencimientos de turno."""

    def _game(self, theme: str = "classic", profile: str = "classic") -> AsyncGame:
        session = AsyncGame.create(
            theme, ["Uno", "Dos", "Tres", "Cuatro"], rules_profile=profile
        )
        self.addCleanup(session.close)
        session.apply({"mensaje": "empezar", "paises_para_victoria": 0})
        session.apply({"mensaje": "empezar_partida"})
        return session

    def test_close_stops_engine_even_if_disk_write_fails(self) -> None:
        """Un error de disco al salir no deja el ejecutor ni el reloj activos."""
        session = self._game()
        with (
            patch.object(session, "save_draft", side_effect=OSError("disco lleno")),
            self.assertRaises(OSError),
        ):
            session.close()
        self.assertIsNone(session.server.serialized(lambda: True))
        session.close()

    def test_all_maps_and_rules_without_network(self) -> None:
        """Las cuatro combinaciones pasan un turno mediante archivo."""
        for theme in ("classic", "revancha"):
            for profile in ("classic", "revancha"):
                with (
                    self.subTest(theme=theme, profile=profile),
                    patch(
                        "socket.socket", side_effect=AssertionError("No debe abrir red")
                    ),
                ):
                    original = self._game(theme, profile)
                    packet = complete_turn(original)
                    receiver = AsyncGame.open(packet)
                    self.addCleanup(receiver.close)
                    self.assertEqual(receiver.user_id, packet["payload"]["holder"])
                    self.assertEqual(receiver.server.theme, theme)
                    self.assertEqual(receiver.server.rules_profile, profile)
                    self.assertIsNone(receiver.server.capture_state()["remaining"])
                    self.assertEqual(
                        receiver.server.public_snapshot()["countries"],
                        original.server.public_snapshot()["countries"],
                    )

    def test_four_player_cycle_detects_duplicates_and_forks(self) -> None:
        """Una vuelta completa vuelve al primer jugador por la misma cadena."""
        original = self._game()
        packet = complete_turn(original)
        first_packet = deepcopy(packet)
        for _player in range(12):
            if packet["payload"]["holder"] == original.user_id:
                break
            receiver = AsyncGame.open(packet)
            self.addCleanup(receiver.close)
            packet = complete_turn(receiver)
        self.assertTrue(original.check_successor(packet))
        self.assertEqual(packet["payload"]["holder"], original.user_id)
        reopened = AsyncGame.open(packet)
        self.addCleanup(reopened.close)
        self.assertFalse(reopened.check_successor(packet))
        altered = deepcopy(first_packet["payload"])
        altered["holder"] = original.user_id
        with self.assertRaises(ValueError):
            reopened.check_successor(make_archive("turn", altered))

    def test_handoff_is_sealed_and_repeated_export_is_identical(self) -> None:
        """Compartir un turno no habilita nuevas acciones en la copia enviada."""
        session = self._game()
        packet = complete_turn(session)
        self.assertEqual(session.export_turn(), packet)
        with self.assertRaises(ValueError):
            session.apply({"mensaje": "finalizar_turno"})

    def test_unfinished_turn_cannot_be_exported(self) -> None:
        """Las validaciones impiden terminar con refuerzos pendientes."""
        session = self._game()
        with self.assertRaises(ValueError):
            session.export_turn()
        result = session.apply({"mensaje": "finalizar_turno"})
        self.assertIsNotNone(result)
        if result:
            self.assertFalse(result["accepted"])

    def test_draft_round_trip_and_command_idempotence(self) -> None:
        """Una acción aceptada mantiene su cache y no se repite tras cargar."""
        session = self._game()
        snapshot = session.server.public_snapshot()
        country = next(
            name
            for name, data in snapshot["countries"].items()
            if data["userid"] == session.user_id
        )
        command = {
            "mensaje": "agregar_unidad",
            "pais": country,
            "tipo_unidad": "infanteria",
            "cantidad": 1,
            "command_id": "one-unit",
        }
        session.apply(command)
        restored = AsyncGame.open(session.draft())
        self.addCleanup(restored.close)
        before = deepcopy(restored.server.public_snapshot())
        restored.apply(command)
        self.assertEqual(before, restored.server.public_snapshot())

    def test_wrong_recipient_and_broken_chain_are_rejected(self) -> None:
        """Un archivo inconsistente no se convierte en una sesión editable."""
        session = self._game()
        payload = complete_turn(session)["payload"]
        payload["holder"] = 999
        with self.assertRaises(ValueError):
            AsyncGame.open(make_archive("turn", payload))
        payload["ancestors"] = ["abc"]
        with self.assertRaises(ValueError):
            AsyncGame.open(make_archive("turn", payload))

    def test_history_is_public_and_reconstructs_missiles_and_owner(self) -> None:
        """La repetición reconstruye el mapa y omite todas las credenciales."""
        session = self._game("revancha", "revancha")
        complete_turn(session)
        history = session.server.serialized(session.server.history.export)
        text = json.dumps(history)
        checkpoint = session.server.capture_state()
        for player in checkpoint["players"]:
            self.assertNotIn(player["token"], text)
        self.assertNotIn("objetivos_asignados", text)
        replay = Replay(history)
        self.assertGreater(replay.count, 1)
        self.assertEqual(
            replay.snapshot(replay.count - 1), session.server.public_snapshot()
        )
        snapshot = replay.snapshot(0)
        snapshot["countries"].clear()
        self.assertTrue(replay.snapshot(0)["countries"])
        self.assertGreater(len(replay.turn_indices()), 1)
