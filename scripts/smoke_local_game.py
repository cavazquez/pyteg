"""Juega con Qt un humano automatizado y tres bots hasta observar victoria."""

# ruff: noqa: S311 -- generadores reproducibles para CI.

from __future__ import annotations

import argparse
import json
import random
import time
from copy import deepcopy
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.bots import BasicBotStrategy
from pyteg.gui.main_window import Gui
from pyteg.gui.managers.window import WindowManager
from pyteg.server.app import Server
from pyteg.server.hosting.engine import ServerEngine
from pyteg.toml_reader import TomlReader

if TYPE_CHECKING:
    from pyteg.client.offline import OfflineConnection
    from pyteg.persistence.local import LocalGame


def play(  # noqa: PLR0915 -- recorrido gráfico completo.
    app: QApplication, theme: str, profile: str, output: Path, timeout: float
) -> dict[str, object]:
    """Usa widgets, eventos privados y el transmisor Qt real en modo local.

    Returns:
        Resultado público de una partida completa.

    Raises:
        RuntimeError: Si no se alcanza una victoria o las proyecciones divergen.

    """
    window = Gui(Client(), map_theme=theme)
    window.sound_manager.set_enabled(False)
    try:
        window.files_manager.show_start()
        app.processEvents()
        start = window.files_manager.start_dialog
        if start:
            start.grab().save(str(output / f"start-{theme}-{profile}.png"))
            start.close()
        random.seed(7)
        engine = ServerEngine(
            partial(
                Server, objective_rng=random.Random(7), situation_rng=random.Random(7)
            )
        )
        with patch("pyteg.persistence.local.ServerEngine", return_value=engine):
            window.files_manager.start_offline(theme, profile, "Humano", 3)
        app.processEvents()
        connection = cast("OfflineConnection", window.conexion)
        game = cast("LocalGame", connection.game)
        connection._bot_timer.setInterval(1)  # noqa: SLF001 -- acelera la espera de CI.
        window.transmisor.empezar(
            segundos=3600, paises_para_victoria=30, objetivos_secretos=False
        )
        window.transmisor.empezar_partida()
        app.processEvents()
        human = BasicBotStrategy(TomlReader.from_theme(theme))
        deadline = time.monotonic() + timeout
        next_report = time.monotonic() + 10
        steps = 0
        while connection.state_model.victory is None and time.monotonic() < deadline:
            app.processEvents()
            if game.holder() == game.user_id:
                before = deepcopy(connection.state_model)
                command = human.next_command(before)
                if command is not None:
                    connection.send_data(json.dumps(command))
                    app.processEvents()
                    results = connection.state_model.command_results
                    result = next(reversed(results.values())) if results else None
                    human.acknowledge(command, result, before, connection.state_model)
                    steps += 1
            QTest.qWait(1)
            if time.monotonic() >= next_report:
                print(
                    json.dumps({
                        "theme": theme,
                        "rules_profile": profile,
                        "progress": game.server.public_snapshot()["turno"],
                        "phase": connection.state_model.last_phase,
                        "commands": steps,
                    }),
                    flush=True,
                )
                next_report = time.monotonic() + 10
        if connection.state_model.victory is None:
            msg = (
                f"Los bots locales no terminaron {theme}/{profile} dentro del límite; "
                f"turno={game.server.public_snapshot()['turno']}, comandos={steps}"
            )
            raise RuntimeError(msg)
        snapshot = game.server.public_snapshot()
        if connection.state_model.snapshot["countries"] != snapshot["countries"]:
            msg = "La interfaz y el motor local no coinciden"
            raise RuntimeError(msg)
        QTest.qWait(30)
        window.grab().save(str(output / f"local-{theme}-{profile}.png"))
        return {
            "status": "passed",
            "theme": theme,
            "rules_profile": profile,
            "players": 4,
            "human_commands": steps,
            "victory": connection.state_model.victory,
            "round": (snapshot.get("turno") or {}).get("num_ronda"),
        }
    finally:
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def main() -> int:
    """Ejecuta las cuatro combinaciones con guardados temporales.

    Returns:
        Cero si las cuatro partidas llegaron a victoria.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/local-games")
    )
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    with (
        TemporaryDirectory(prefix="pyteg-local-smoke-") as directory,
        patch(
            "pyteg.gui.managers.files.QStandardPaths.writableLocation",
            return_value=directory,
        ),
        patch("pyteg.client.tasks.game_flow.partida.open_message_box"),
        patch.object(
            WindowManager,
            "show_battle_result_dialog",
            side_effect=lambda _data, finished: finished(),
        ),
    ):
        for theme in ("classic", "revancha"):
            for profile in ("classic", "revancha"):
                # El motor productivo usa secrets para dados y colores.
                # La prueba conserva esas reglas y fija sólo la aleatoriedad.
                with (
                    patch("secrets.randbelow", random.Random(7).randrange),
                    patch("secrets.choice", random.Random(7).choice),
                ):
                    report = play(
                        cast("QApplication", app),
                        theme,
                        profile,
                        args.output_dir,
                        args.timeout,
                    )
                print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
