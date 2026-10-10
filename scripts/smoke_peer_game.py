"""Cuatro ventanas Qt entre pares: reparto, turnos, combate, caída y reconexión."""

from __future__ import annotations

import argparse
import gc
import json
import time
from copy import deepcopy
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.bots import BasicBotStrategy
from pyteg.client.peer_connection import PeerConnection
from pyteg.gui.main_window import Gui
from pyteg.gui.managers.window import WindowManager
from pyteg.network.peer_runtime import PeerNode
from pyteg.persistence.archive import FileRepository
from pyteg.toml_reader import TomlReader
from scripts.smoke_qt_multiclient import (
    _wait_for,  # noqa: PLC2701 -- espera Qt compartida.
)

if TYPE_CHECKING:
    from collections.abc import Callable

_PLAYERS = 4
_AFTER_CRASH = 3


def node(window: Gui) -> PeerNode:
    """Obtiene el nodo conectado.

    Returns:
        Nodo preparado de la ventana.

    Raises:
        RuntimeError: Si terminó la conexión.

    """
    result = connection(window).node
    if result is None:
        msg = "La conexión terminó"
        raise RuntimeError(msg)
    return result


def ready(peer: PeerConnection) -> bool:
    """Indica si se recibió la identidad Qt.

    Returns:
        True cuando el motor y la proyección están preparados.

    """
    return peer.node is not None and peer.state_model.local_userid is not None


def connection(window: Gui) -> PeerConnection:
    """Obtiene una conexión Qt preparada y su réplica local.

    Returns:
        La conexión activa entre pares.

    Raises:
        RuntimeError: Si todavía no está conectada.

    """
    peer = window.conexion
    if not isinstance(peer, PeerConnection) or peer.node is None:
        msg = "La ventana no está conectada entre pares"
        raise RuntimeError(msg)
    return peer


def play(  # noqa: C901, PLR0914, PLR0915 -- recorrido gráfico con caída y reincorporación.
    app: QApplication, theme: str, profile: str, output: Path
) -> dict[str, object]:
    """Juega acciones reales y recupera al creador contactando otro participante.

    Returns:
        Evidencia pública del escenario completado.

    Raises:
        RuntimeError: Si divergen los estados o no se observa un combate.

    """
    windows: list[Gui] = []

    def wait(predicate: Callable[[], bool], description: str) -> None:
        _wait_for(app, predicate, 25, description)

    def send(window: Gui, command: dict[str, object], command_id: str) -> None:
        peer = connection(window)
        errors: list[str] = []
        peer.failed.connect(errors.append)
        try:
            peer.send_data(json.dumps({**command, "command_id": command_id}))
            wait(
                lambda: command_id in peer.state_model.command_results or bool(errors),
                command_id,
            )
            if errors:
                msg = f"{command_id} ({command['mensaje']}): {errors[-1]}"
                raise RuntimeError(msg)
        finally:
            peer.failed.disconnect(errors.append)

    try:
        for index in range(4):
            window = Gui(Client(), map_theme=theme)
            window.sound_manager.set_enabled(False)
            window.show()
            windows.append(window)
            if window.files_manager.start_dialog:
                window.files_manager.start_dialog.close()
            peer = PeerConnection(window)
            repository = FileRepository(
                window.files_manager.save_directory
                / f"peer-{theme}-{profile}-{index}.pyteg"
            )
            if index == 0:
                peer.start(
                    partial(
                        PeerNode.create,
                        theme,
                        "Jugador 1",
                        profile,
                        repository=repository,
                    )
                )
            else:
                address = "127.0.0.1", node(windows[index - 1]).port
                name = f"Jugador {index + 1}"
                peer.start(
                    partial(
                        PeerNode.join,
                        address,
                        name,
                        repository=repository,
                        invitation=node(windows[index - 1]).invitation("127.0.0.1"),
                    )
                )
            wait(
                partial(ready, peer),
                "identidad Qt",
            )
        send(
            windows[0],
            {"mensaje": "empezar", "segundos": 120, "paises_para_victoria": 0},
            "config-peer",
        )
        send(windows[0], {"mensaje": "empezar_partida"}, "start-peer")
        wait(
            lambda: all(
                connection(window).state_model.snapshot.get("estado") == "JUGANDO"
                for window in windows
            ),
            "reparto en cuatro mapas Qt",
        )
        windows[0].grab().save(str(output / f"peer-{theme}-{profile}.png"))
        strategies = [
            BasicBotStrategy(TomlReader.from_theme(theme)) for _window in windows
        ]
        attacks = 0
        steps = 0
        deadline = time.monotonic() + 180
        while attacks == 0 and time.monotonic() < deadline:
            app.processEvents()
            current = connection(windows[0]).state_model.snapshot["turno"]["jugador_id"]
            window = windows[current - 1]
            peer = connection(window)
            before = deepcopy(peer.state_model)
            command = strategies[current - 1].next_command(before)
            if command is None:
                time.sleep(0.01)
                continue
            command_id = f"peer-smoke-{steps}"
            send(window, command, command_id)
            result = peer.state_model.command_results[command_id]
            strategies[current - 1].acknowledge(
                command, result, before, peer.state_model
            )
            attacks += int(
                command["mensaje"] == "atacar" and result.get("accepted") is True
            )
            steps += 1
        if attacks == 0:
            msg = f"No se observó combate entre pares después de {steps} acciones"
            raise RuntimeError(msg)
        creator = connection(windows[0])
        saved = node(windows[0]).draft()
        creator.desconectar()
        wait(
            lambda: all(
                len(node(window).document["state"]["members"]) == _AFTER_CRASH
                for window in windows[1:]
            ),
            "baja del creador en tres réplicas",
        )
        send(
            windows[2],
            {"mensaje": "chat", "msg": "Seguimos sin el creador"},
            "after-creator",
        )
        if any(window.host_runtime is not None for window in windows):
            msg = "El modo entre pares creó un anfitrión de juego"
            raise RuntimeError(msg)
        target = connection(windows[3]).node
        if target is None:
            msg = "Falta el par para reincorporarse"
            raise RuntimeError(msg)
        restored = PeerConnection(windows[0])
        restore_errors: list[str] = []
        restored.failed.connect(restore_errors.append)
        identity = saved["payload"]["peer"]
        restored.start(
            lambda: PeerNode.join(
                ("127.0.0.1", target.port),
                "Jugador 1",
                identity=(1, identity["private_key"]),
                saved_archive=saved,
                invitation=target.invitation("127.0.0.1"),
            )
        )
        wait(
            lambda: restored.node is not None or bool(restore_errors),
            "reconexión a través del cuarto jugador",
        )
        if restore_errors:
            msg = f"La reconexión entre pares falló: {restore_errors[-1]}"
            raise RuntimeError(msg)
        wait(
            lambda: all(
                len(node(window).document["state"]["members"]) == _PLAYERS
                for window in windows
            ),
            "reincorporación en las cuatro réplicas",
        )
        wait(
            lambda: all(
                connection(window).state_model.snapshot.get("countries")
                == connection(windows[0]).state_model.snapshot.get("countries")
                for window in windows
            ),
            "mapas Qt iguales después de reconectar",
        )
        windows[0].grab().save(str(output / f"peer-restored-{theme}-{profile}.png"))
        return {
            "status": "passed",
            "theme": theme,
            "rules_profile": profile,
            "players": 4,
            "commands": steps,
            "attacks": attacks,
            "creator_rejoined": True,
        }
    finally:
        for window in windows:
            window.close()
            window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        # Recolectar los ciclos de wrappers Qt en el hilo gráfico antes de
        # que las asignaciones del motor siguiente activen el GC en un worker.
        gc.collect()


def main() -> int:
    """Ejecuta un escenario o las cuatro combinaciones de mapa y perfil.

    Returns:
        Cero si todos los escenarios terminan correctamente.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("classic", "revancha"))
    parser.add_argument("--rules-profile", choices=("classic", "revancha"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/peer-games"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with (
        TemporaryDirectory(prefix="pyteg-peer-smoke-") as directory,
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
        for theme in (args.theme,) if args.theme else ("classic", "revancha"):
            for profile in (
                (args.rules_profile,) if args.rules_profile else ("classic", "revancha")
            ):
                print(
                    json.dumps(
                        play(app, theme, profile, args.output_dir), ensure_ascii=False
                    ),
                    flush=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
