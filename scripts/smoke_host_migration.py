# ruff: noqa: SLF001
"""Cuatro clientes Qt, caída abrupta del anfitrión y dos migraciones reales.

El primer cliente vive en otro proceso: ``kill`` termina también sus hilos y
sockets sin guardar nada. Los otros tres recuperan la partida desde su copia.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # noqa: S404 -- inicia únicamente el cliente local de prueba.
import sys
import tempfile
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.conexion.connection import ConnectionClient
from pyteg.gui import Gui
from pyteg.gui.dialogs.conectar import VentanaConectar
from scripts.smoke_qt_multiclient import (
    _free_port,  # noqa: PLC2701 -- helper compartido del smoke Qt.
    _wait_for,  # noqa: PLC2701 -- helper compartido del smoke Qt.
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.client.state_model import ClientStateModel
    from pyteg.server.app import Server

_CLIENTS = 4
_SECOND_PLAYER = 2
_TIMEOUT = 25.0


def _window(
    theme: str, port: int, name: str, *, hosting: bool, invitation: str = ""
) -> Gui:
    window = Gui(Client(), map_theme=theme)
    window.sound_manager.set_enabled(False)
    window.hide()
    window.sound_manager.set_enabled(enabled=False)
    dialog = VentanaConectar(window)
    window.ventana_conectar = dialog
    dialog.addr.setText("127.0.0.1")
    dialog.port.setText(str(port))
    dialog.username.setText(name)
    dialog.invitation_entry.setText(invitation)
    if hosting:
        dialog.mode_selector.setCurrentIndex(1)
    dialog.connect_to_server()
    return window


def _server(window: Gui) -> Server:
    if window.host_runtime is None or window.host_runtime.server is None:
        msg = "La ventana todavía no es anfitriona"
        raise RuntimeError(msg)
    return window.host_runtime.server


def _fixture(server: Server) -> None:
    """Prepara cartas y un misil para verificar su conservación en la migración.

    Raises:
        RuntimeError: Si la partida todavía no comenzó.

    """
    game = server.game
    if game is None:
        msg = "No se inició la partida de prueba"
        raise RuntimeError(msg)
    game.finalizar_turno()
    country = next(
        country
        for country in server.mapa.paises()
        if server.mapa.ocupado_por(country) == _SECOND_PLAYER
    )
    server.mapa._mapa[country].misiles = 1
    for player in server.dame_clientes():
        game.mazo().asignar_tarjeta(player)
        server.enviar_tarjetas_jugador(player)
    server.enviar_turno_actual()
    server.bump_state_revision()
    server.enviar_snapshot()


def _worker(args: argparse.Namespace) -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = _window(args.theme, args.port, "Anfitrión inicial", hosting=True)
    stage = 0

    def progress() -> None:
        nonlocal stage
        if window.host_runtime is None:
            return
        server = _server(window)
        if (
            window.client.userid() is not None
            and window.client.reconnect_token() is not None
        ):
            ready = Path(args.ready_file)
            if not ready.exists():
                ready.write_text(
                    window.host_runtime.invitation("127.0.0.1").encode(),
                    encoding="utf-8",
                )
        if (
            stage == 0
            and server.cant_clients() == _CLIENTS
            and all(
                client.handshake_status() is True for client in server.dame_clientes()
            )
        ):
            stage = 1
            window.transmisor.empezar(
                segundos=90,
                paises_para_victoria=0,
                objetivos_secretos=True,
                misiles_habilitados=True,
                rules_profile=args.rules_profile,
            )
        elif stage == 1 and server.estado.es_esperando_jugadores():
            stage = 2
            window.transmisor.empezar_partida()
        elif stage == _SECOND_PLAYER and server.estado.es_jugando():
            stage = 3
            server._command_executor.call_serialized(lambda: _fixture(server))

    timer = QTimer(window)
    timer.setInterval(50)
    timer.timeout.connect(progress)
    timer.start()
    return app.exec()


def _connection(window: Gui) -> ConnectionClient:
    if not isinstance(window.conexion, ConnectionClient):
        msg = "Se perdió la conexión Qt de la prueba"
        raise RuntimeError(msg)  # noqa: TRY004 -- falla de ciclo de vida.
    return window.conexion


def _model(window: Gui) -> ClientStateModel:
    model = window.client_state_model
    if model is None:
        msg = "Todavía no se recibió el estado del cliente"
        raise RuntimeError(msg)
    return model


def _has_token(client: Client) -> bool:
    return client.reconnect_token() is not None


def _checkpoint(window: Gui) -> dict[str, Any]:
    if window.host_runtime is None:
        return {}
    return window.host_runtime.latest_checkpoint() or {}


def _confirmed_host(windows: list[Gui]) -> Gui | None:
    """Obtiene el anfitrión que coincide con la autoridad de todas las réplicas.

    Returns:
        Ventana del anfitrión confirmado o None mientras las copias difieren.

    """
    if not windows:
        return None
    authority = {
        (_checkpoint(window).get("epoch"), _checkpoint(window).get("owner_id"))
        for window in windows
    }
    if len(authority) != 1:
        return None
    epoch, owner = authority.pop()
    for window in windows:
        runtime = window.host_runtime
        if runtime is None or runtime.server is None or window.client.userid() != owner:
            continue
        replication = runtime.server.host_replication
        if replication is not None and (replication.epoch, replication.owner_id) == (
            epoch,
            owner,
        ):
            return window
    return None


def _send_unit(window: Gui, country: str, command_id: str) -> None:
    _connection(window).send_data(
        json.dumps({
            "mensaje": "agregar_unidad",
            "pais": country,
            "tipo_unidad": "infanteria",
            "cantidad": 1,
            "command_id": command_id,
        })
    )


def _require(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _require_host(windows: list[Gui]) -> Gui:
    """Obtiene el dueño confirmado o interrumpe el escenario inconsistente.

    Returns:
        Ventana del anfitrión vigente.

    """
    host = _confirmed_host(windows)
    _require(host is not None, "Las réplicas no coinciden en el anfitrión vigente")
    return cast("Gui", host)


def _run(args: argparse.Namespace) -> int:  # noqa: PLR0914, PLR0915 -- escenario de dos migraciones.
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    port = _free_port()
    windows: list[Gui] = []
    temporary = tempfile.TemporaryDirectory(prefix="pyteg-host-smoke-")
    ready_file = Path(temporary.name) / "ready"
    worker_log_path = Path(temporary.name) / "worker.log"
    worker_log = worker_log_path.open("w")
    worker = subprocess.Popen(  # noqa: S603 -- ejecutable y script locales.
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--port",
            str(port),
            "--theme",
            args.theme,
            "--rules-profile",
            args.rules_profile,
            "--ready-file",
            str(ready_file),
        ],
        stdout=subprocess.DEVNULL,
        stderr=worker_log,
    )

    def wait(predicate: Callable[[], bool], description: str) -> None:
        _wait_for(app, predicate, _TIMEOUT, description)

    try:
        wait(
            lambda: worker.poll() is not None or ready_file.exists(),
            "anfitrión inicial",
        )
        _require(
            worker.poll() is None, "El proceso anfitrión terminó antes de crear la sala"
        )
        for index in range(3):
            window = _window(
                args.theme,
                port,
                f"Participante {index + 2}",
                hosting=False,
                invitation=ready_file.read_text(encoding="utf-8"),
            )
            windows.append(window)
            wait(partial(_has_token, window.client), "identidad y token")
        wait(
            lambda: all(
                len(_checkpoint(window).get("peers", [])) == _CLIENTS
                and _checkpoint(window).get("checkpoint", {}).get("game") is not None
                and window.client_state_model is not None
                and _model(window).private_cards
                for window in windows
            ),
            "copias privadas en tres clientes Qt",
        )
        identities = [window.client.userid() for window in windows]
        wait(
            lambda: (
                windows[0].client_state_model is not None
                and windows[0]
                .client_state_model.snapshot.get("turno", {})
                .get("jugador_id")
                == _SECOND_PLAYER
            ),
            "turno del sucesor",
        )
        country = next(
            name
            for name, data in _model(windows[0]).snapshot["countries"].items()
            if data["userid"] == _SECOND_PLAYER
        )
        command_id = "host-migration-first-unit"
        _send_unit(windows[0], country, command_id)
        wait(
            lambda: (
                command_id in _model(windows[0]).command_results
                and all(
                    any(
                        command_id in player["cache"]
                        for player in _checkpoint(window)["checkpoint"]["players"]
                        if player["userid"] == _SECOND_PLAYER
                    )
                    for window in windows
                )
            ),
            "comando aplicado y replicado",
        )
        model = _model(windows[0])
        _require(
            model.command_results[command_id]["accepted"],
            "Se rechazó el refuerzo inicial",
        )
        countries = deepcopy(model.snapshot["countries"])
        private = [
            (
                deepcopy(_model(window).private_cards),
                deepcopy(_model(window).private_objective),
            )
            for window in windows
        ]
        initial_epoch = _checkpoint(windows[0])["epoch"]
        worker.kill()
        worker.wait(timeout=5)
        wait(
            lambda: all(
                _checkpoint(window).get("epoch", -1) > initial_epoch
                and window.conexion is not None
                and window.conexion.esta_conectado()
                for window in windows
            ),
            "primera migración después de kill",
        )
        wait(
            lambda: (
                all(not _connection(window).hosting.paused for window in windows)
                and _confirmed_host(windows) is not None
            ),
            "reanudación del reloj",
        )
        successor = _require_host(windows)
        _require(
            not _server(successor).host_migrating, "El sucesor no reanudó la partida"
        )
        _require(
            identities == [window.client.userid() for window in windows],
            "Cambió la identidad de un jugador",
        )
        _require(
            countries == _model(windows[0]).snapshot["countries"],
            "Cambió la ocupación, unidades o misiles",
        )
        for window, expected in zip(windows, private, strict=True):
            _require(
                (
                    _model(window).private_cards,
                    _model(window).private_objective,
                )
                == expected,
                "Cambiaron cartas u objetivos privados",
            )
        _model(windows[0]).command_results.pop(command_id, None)
        _send_unit(windows[0], country, command_id)
        wait(
            lambda: command_id in _model(windows[0]).command_results,
            "reintento idempotente",
        )
        _require(
            _model(windows[0]).snapshot["countries"][country] == countries[country],
            "El reintento aplicó el refuerzo dos veces",
        )
        _send_unit(windows[0], country, "host-migration-second-unit")
        wait(
            lambda: all(
                _model(window).snapshot["countries"][country]["unidades"]
                == countries[country]["unidades"] + 1
                for window in windows
            ),
            "nueva acción con el sucesor",
        )
        successor = _require_host(windows)
        first_epoch = _checkpoint(successor)["epoch"]
        _connection(successor).desconectar()
        survivors = [window for window in windows if window is not successor]
        remaining_identities = [window.client.userid() for window in survivors]
        wait(
            lambda: (
                all(
                    _checkpoint(window).get("epoch", -1) > first_epoch
                    for window in survivors
                )
                and _confirmed_host(survivors) is not None
            ),
            "segunda migración",
        )
        wait(
            lambda: (
                all(not _connection(window).hosting.paused for window in survivors)
                and any(
                    window.host_runtime is not None
                    and window.host_runtime.server is not None
                    for window in survivors
                )
            ),
            "continuación con el tercer anfitrión",
        )
        _require(
            remaining_identities == [window.client.userid() for window in survivors],
            "Cambió la identidad en la segunda migración",
        )
        _require(
            any(
                window.host_runtime is not None
                and window.host_runtime.server is not None
                and window.host_runtime.server.estado.es_jugando()
                for window in survivors
            ),
            "La segunda migración cerró la partida",
        )
        print(
            f"Host migration OK: mapa={args.theme}, reglas={args.rules_profile}; "
            "4 clientes Qt, kill del anfitrión, 2 migraciones, "
            "estado privado conservado y acciones idempotentes."
        )
    except Exception:
        print("Worker status:", worker.poll())
        for window in windows:
            print(
                "Client status:",
                window.client.userid(),
                window.estado_actual,
                len(_checkpoint(window).get("peers", [])),
                len(_model(window).private_cards),
            )
        worker_log.flush()
        print(worker_log_path.read_text()[-6000:])
        raise
    else:
        return 0
    finally:
        for window in windows:
            window.close()
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=5)
        worker_log.close()
        temporary.cleanup()


def main() -> int:
    """Ejecuta el smoke con el mapa y perfil de reglas elegidos.

    Returns:
        Cero si los cuatro clientes superan las dos migraciones.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("classic", "revancha"), default="classic")
    parser.add_argument(
        "--rules-profile", choices=("classic", "revancha"), default="classic"
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=65432, help=argparse.SUPPRESS)
    parser.add_argument("--ready-file", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return _worker(args) if args.worker else _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
