"""Juega una partida corta con ventanas Qt y transporte TCP real.

El smoke acepta ambos mapas y perfiles, varias instancias reales de ``Gui`` y el mismo
modelo Qt que usa el cliente distribuido. Configura e inicia la partida,
coloca refuerzos, conquista un país, reconecta una ventana durante la partida
y observa la victoria desde todos los clientes. El render de las imágenes
del tablero se desacopla en el backend ``offscreen`` para mantener el recorrido
acotado; el smoke visual de conexión cubre la construcción del mapa. Los dados
se fijan sólo en el proceso servidor para que CI tenga un recorrido repetible.

Uso desde la raíz del repositorio::

    QT_QPA_PLATFORM=offscreen uv run python scripts/smoke_qt_game.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import socket
import subprocess  # noqa: S404 -- sólo inicia el servidor local del smoke
import sys
import time
import tomllib
import uuid
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, cast
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget

from pyteg.client.app import Client
from pyteg.client.conexion.connection import ConnectionClient
from pyteg.client.state_adapter import QtClientStateAdapter
from pyteg.client.tasks.game_flow.partida import ClientTaskVictoria
from pyteg.client.tasks.lobby.chat import ClientTaskError
from pyteg.gui import Gui
from pyteg.gui.dialogs.conectar import VentanaConectar
from pyteg.gui.dialogs.dice_animation import BattleResultDialog
from pyteg.gui.managers.window import WindowManager
from pyteg.toml_reader import TomlReader
from scripts.secure_fixture import server_invitation

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.network.security import Invitation
    from pyteg.server.hosting.runtime import HostRuntime

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT = 45.0
DEFAULT_SEED = 7
MIN_COMBAT_ROUND = 3
RECONNECT_ROUND = 2
CLIENT_COUNT = 3
MIN_CLIENTS = 3
MAX_CLIENTS = 8
DEBUG = bool(os.environ.get("PYTEG_QT_SMOKE_DEBUG"))


def _trace(message: str) -> None:
    """Emitir trazas opcionales del smoke sin contaminar la evidencia JSON."""
    if DEBUG:
        print(f"[qt-smoke] {message}", file=sys.stderr, flush=True)


def _server_listening(port: int) -> bool:
    """Comprueba si el servidor local ya acepta conexiones.

    Returns:
        ``True`` si el puerto acepta una conexión TCP.

    """
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def _connect_window(  # noqa: PLR0913 -- configuración del cliente Qt de prueba.
    client: Client,
    port: int,
    theme: str,
    username: str,
    *,
    invitation: Invitation,
    runtime: HostRuntime | None = None,
    visible: bool = False,
) -> Gui:
    """Crea una ventana Qt de juego y la conecta al servidor local.

    Returns:
        Ventana Qt conectada al servidor.

    """
    window = Gui(client, map_theme=theme)
    window.sound_manager.set_enabled(False)
    window.hide()
    dialog = VentanaConectar(window)
    window.ventana_conectar = dialog
    dialog.addr.setText("127.0.0.1")
    dialog.port.setText(str(port))
    dialog.username.setText(username)
    dialog.invitation_entry.setText(invitation.encode())
    if runtime is not None:
        user_id = client.userid()
        if user_id is not None:
            dialog._saved_identity = user_id, runtime.identity.export_private()  # noqa: SLF001 -- misma identidad del recorrido de prueba.
    dialog.connect_to_server()
    if visible:
        window.resize(1024, 720)
        window.show()
    return window


def _close_windows(app: QApplication, windows: list[Gui]) -> None:
    """Desconecta y cierra todas las ventanas creadas por el smoke."""
    for window in windows:
        connection = window.conexion
        if isinstance(connection, ConnectionClient):
            connection.desconectar()
        window.close()
    app.processEvents()


def _stop_process(process: subprocess.Popen[str]) -> None:
    """Termina el proceso servidor y aplica un límite al cierre."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _fail(message: str) -> NoReturn:
    """Interrumpe el smoke con un diagnóstico estable.

    Raises:
        RuntimeError: Siempre, con el diagnóstico recibido.

    """
    raise RuntimeError(message)


def _parse_args() -> argparse.Namespace:
    """Parsea los parámetros del smoke Qt de partida completa.

    Returns:
        Argumentos validados de la línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Partida Qt con ambos mapas, perfiles, situaciones y reconexión.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--theme", choices=("classic", "revancha"), default="classic")
    parser.add_argument("--rules-profile", choices=("classic", "revancha"))
    parser.add_argument("--clients", type=int, default=CLIENT_COUNT)
    parser.add_argument("--visible", action="store_true", help="Muestra las ventanas.")
    parser.add_argument(
        "--render-map",
        action="store_true",
        help="Renderiza cada cambio del mapa incluso en offscreen.",
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Guarda capturas de la carta y el mapa."
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout debe ser positivo")
    if not MIN_CLIENTS <= args.clients <= MAX_CLIENTS:
        parser.error("--clients debe estar entre 3 y 8")
    args.rules_profile = args.rules_profile or args.theme
    return args


def _free_port() -> int:
    """Obtiene un puerto efímero para el proceso servidor del smoke.

    Returns:
        Puerto libre en loopback.

    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _start_server(
    port: int, seed: int, theme: str, environment: dict[str, str]
) -> subprocess.Popen[str]:
    """Inicia el entry point de servidor determinista usado por CI.

    Returns:
        Proceso servidor con salida combinada disponible para diagnóstico.

    """
    return subprocess.Popen(  # noqa: S603 -- argumentos estáticos del smoke
        [
            sys.executable,
            str(ROOT / "scripts" / "simulate_game.py"),
            "--server-child",
            str(port),
            "--theme",
            theme,
            "--seed",
            str(seed),
            "--deterministic-dice",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _load_adjacency(theme: str) -> dict[str, tuple[str, ...]]:
    """Carga las adyacencias públicas del mapa que usa el smoke.

    Returns:
        Adyacencias dirigidas normalizadas a tuplas.

    """
    path = ROOT / "themes" / theme / "adyacencias.toml"
    with path.open("rb") as file:
        raw = tomllib.load(file).get("Adyacencias", {})
    return {
        str(country): tuple(
            str(neighbor) for neighbor in neighbors if isinstance(neighbor, str)
        )
        for country, neighbors in raw.items()
        if isinstance(country, str) and isinstance(neighbors, list)
    }


def _wait_for(
    app: QApplication,
    predicate: Callable[[], bool],
    timeout: float,
    description: str,
) -> None:
    """Procesa eventos Qt hasta que se cumple una condición."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    app.processEvents()
    if not predicate():
        _fail(f"Timeout esperando {description}")


def _connection(window: Gui) -> ConnectionClient:
    """Obtiene la conexión Qt activa de una ventana.

    Returns:
        Conexión Qt activa.

    Raises:
        TypeError: Si la ventana no tiene una conexión Qt activa.

    """
    connection = window.conexion
    if not isinstance(connection, ConnectionClient):
        message = "La ventana Qt no tiene una conexión activa"
        raise TypeError(message)
    return connection


def _snapshot(window: Gui) -> dict[str, Any]:
    """Obtiene el snapshot público reconstruido por la conexión Qt.

    Returns:
        Copia del snapshot público actual.

    """
    return dict(_connection(window).state_model.snapshot)


def _country_state(window: Gui) -> dict[str, dict[str, Any]]:
    """Obtiene países del snapshot con una forma estable para el smoke.

    Returns:
        Países y sus datos públicos normalizados.

    """
    countries = _snapshot(window).get("countries", {})
    if not isinstance(countries, dict):
        return {}
    return {
        str(name): dict(country)
        for name, country in countries.items()
        if isinstance(name, str) and isinstance(country, dict)
    }


def _send_command(
    app: QApplication,
    window: Gui,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """Envía un comando por ``ConnectionClient`` y espera su resultado.

    Returns:
        Resultado aceptado por el servidor.

    """
    connection = _connection(window)
    _trace(f"send {payload.get('mensaje')}")
    command_id = uuid.uuid4().hex
    command = dict(payload)
    command["command_id"] = command_id
    connection.send_data(json.dumps(command, ensure_ascii=False))

    result: dict[str, Any] | None = None

    def has_result() -> bool:
        nonlocal result
        raw = connection.state_model.command_results.get(command_id)
        if isinstance(raw, dict):
            result = raw
            return True
        return False

    _wait_for(app, has_result, timeout, f"resultado de {payload.get('mensaje')}")
    if result is None or result.get("accepted") is not True:
        error = result.get("error_code") if result else "sin resultado"
        _fail(f"Comando Qt rechazado: {payload.get('mensaje')} ({error})")
    _trace(f"accepted {payload.get('mensaje')}")
    return result


def _wait_convergence(app: QApplication, windows: list[Gui], timeout: float) -> None:
    """Espera que todas las ventanas actuales tengan el mismo tablero."""

    def converged() -> bool:
        boards = [
            json.dumps(_country_state(window), sort_keys=True)
            for window in windows
            if window.conexion is not None
        ]
        cards = [
            json.dumps(_snapshot(window).get("situacion"), sort_keys=True)
            for window in windows
            if window.conexion is not None
        ]
        return (
            len(boards) == len(windows)
            and len(set(boards)) == 1
            and len(set(cards)) == 1
        )

    _wait_for(app, converged, timeout, "convergencia del tablero Qt")


def _active_window(windows: list[Gui], user_id: int) -> Gui:
    """Resuelve la ventana Qt que posee el turno anunciado.

    Returns:
        Ventana Qt del jugador activo.

    """
    for window in windows:
        if window.client.userid() == user_id and window.conexion is not None:
            return window
    _fail(f"No hay ventana Qt activa para el jugador {user_id}")


def _show_battle_non_blocking(
    manager: WindowManager,
    battle_data: dict[str, Any],
    on_finished: Callable[[], None],
) -> None:
    """Muestra la animación real y cierra el diálogo automáticamente en CI."""
    dialog = BattleResultDialog(battle_data, cast("QWidget", manager.main_window))
    dialog.animation_finished.connect(on_finished)
    dialog.show()
    QTimer.singleShot(4_000, dialog.accept)


def _skip_country_render(
    _adapter: QtClientStateAdapter,
    _state: dict[str, Any],
    _names: set[str] | None = None,
    **_options: Any,
) -> None:
    """Evita el coste del render del tablero en el backend offscreen."""


def _report_client_error(task: ClientTaskError, _window: Any) -> None:
    """Registra errores de protocolo sin abrir diálogos modales en CI."""
    _trace(
        "client error "
        f"{getattr(task, '_error_type', None)}: {getattr(task, '_message', None)}"
    )


def _report_victory(task: ClientTaskVictoria, _window: Any) -> None:
    """Registra la victoria sin abrir los diálogos modales del cliente."""
    _trace(
        "victory event "
        f"winner={getattr(task, '_ganador_id', None)} "
        f"name={getattr(task, '_ganador_nombre', None)}"
    )


def _reconnect_client(  # noqa: PLR0913, PLR0917
    app: QApplication,
    port: int,
    client: Client,
    current_window: Gui,
    all_windows: list[Gui],
    timeout: float,
) -> Gui:
    """Reemplaza una ventana Qt conservando su identidad criptográfica.

    Returns:
        Nueva ventana Qt autenticada con la misma identidad.

    """
    _trace("reconnect start")
    user_id = client.userid()
    if user_id is None or not client.reconnect_token():
        _fail("El cliente Qt no tiene identidad o token para reconectar")
    connection = _connection(current_window)
    invitation = connection.invitation
    runtime = current_window.host_runtime
    if invitation is None or runtime is None:
        _fail("El cliente no conserva su invitación e identidad segura")
    connection.desconectar()
    _wait_for(
        app,
        lambda: current_window.conexion is None,
        timeout,
        "desconexión de la segunda ventana Qt",
    )
    _wait_for(
        app,
        lambda: any(
            player.get("userid") == user_id and not player.get("connected", True)
            for player in _snapshot(all_windows[0]).get("players", [])
            if isinstance(player, dict)
        ),
        timeout,
        "confirmación de desconexión en el servidor Qt",
    )
    visible = current_window.isVisible()
    current_window.close()

    replacement = _connect_window(
        client,
        port,
        current_window.map_theme,
        "QtGame2-Reconnected",
        visible=visible,
        invitation=invitation,
        runtime=runtime,
    )
    all_windows.append(replacement)
    _wait_for(
        app,
        lambda: (
            replacement.conexion is not None
            and replacement.client.userid() == user_id
            and replacement.conexion.state_model.local_userid == user_id
            and replacement.conexion.state_model.snapshot.get("estado") == "JUGANDO"
        ),
        timeout,
        "reconexión Qt autenticada durante la partida",
    )
    _trace("reconnect done")
    return replacement


def _verify_situation(windows: list[Gui]) -> None:
    """Comprueba la carta real y sus dados después de una reconexión."""
    for window in windows:
        state = _snapshot(window)
        card = state.get("situacion") or {}
        rolls = card.get("tiradas_crisis") or {}
        banner = window.situation_banner
        if card.get("id") != "crisis_1" or not rolls:
            _fail("No se recibió la carta Crisis con sus tiradas públicas")
        lowest = min(rolls.values())
        affected = sorted(
            int(userid) for userid, value in rolls.items() if value == lowest
        )
        if sorted(card.get("jugadores_afectados", [])) != affected:
            _fail("La carta Qt no identifica todos los mínimos de Crisis")
        if (
            banner is None
            or banner.isHidden()
            or "Crisis" not in banner.title_label.text()
        ):
            _fail("La carta recibida no aparece en la ventana Qt")
        if not banner.details_label.text():
            _fail("La carta Qt no explica los jugadores afectados")


def _capture_windows(
    windows: list[Gui], output_dir: Path, theme: str, profile: str
) -> None:
    """Guarda evidencia visual de la situación y el tablero completo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, window in enumerate(windows, start=1):
        path = output_dir / f"{theme}-{profile}-client-{index}.png"
        if not window.grab().save(str(path)):
            _fail(f"No se pudo guardar la captura Qt: {path}")


def _play_game(  # noqa: C901, PLR0912, PLR0914, PLR0915
    app: QApplication,
    port: int,
    args: argparse.Namespace,
    invitation: Invitation,
) -> dict[str, Any]:
    """Configura, juega y valida la partida con las ventanas solicitadas.

    Returns:
        Evidencia serializable de victoria, turnos y reconexión.

    """
    _trace("creating clients")
    timeout = args.timeout
    clients = [Client() for _ in range(args.clients)]
    all_windows: list[Gui] = []
    windows: list[Gui] = []
    for index, client in enumerate(clients, start=1):
        window = _connect_window(
            client,
            port,
            args.theme,
            f"QtGame{index}",
            visible=args.visible,
            invitation=invitation,
        )
        all_windows.append(window)
        windows.append(window)

    try:
        _wait_for(
            app,
            lambda: (
                all(
                    window.conexion is not None and window.client.userid() is not None
                    for window in windows
                )
                and any(window.client.es_admin() for window in windows)
            ),
            timeout,
            "handshake de las ventanas Qt",
        )
        _trace("handshake done")
        admin = next(window for window in windows if window.client.es_admin())
        reader = TomlReader.from_theme(args.theme)
        victory_target = math.ceil(len(reader.todos_los_paises()) / args.clients) + 1
        _send_command(
            app,
            admin,
            {
                "mensaje": "empezar",
                "segundos": 60,
                "paises_para_victoria": victory_target,
                "objetivos_secretos": False,
                "misiles_habilitados": False,
                "rules_profile": args.rules_profile,
                "situations_enabled": True,
                "situation_card_ids": ["crisis_1"],
            },
            timeout,
        )
        _send_command(app, admin, {"mensaje": "empezar_partida"}, timeout)
        _wait_for(
            app,
            lambda: all(
                _snapshot(window).get("estado") == "JUGANDO" for window in windows
            ),
            timeout,
            "inicio de partida Qt",
        )
        _trace("game started")
        for window in windows:
            state = _snapshot(window)
            if (
                state.get("theme") != args.theme
                or state.get("configuracion", {}).get("rules_profile")
                != args.rules_profile
                or window.scene is None
                or window.scene.map_theme != args.theme
            ):
                _fail("La ventana Qt no conserva la combinación de mapa y reglas")
        country_names = tuple(_country_state(windows[0]))
        adjacency = _load_adjacency(args.theme)

        turns = 0
        conquests = 0
        reconnected = False
        situation_verified = False
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            app.processEvents()
            reference = _snapshot(windows[0])
            if reference.get("estado") == "Finalizado":
                break
            turn = reference.get("turno")
            if not isinstance(turn, dict):
                time.sleep(0.01)
                continue
            active_id = turn.get("jugador_id")
            if not isinstance(active_id, int):
                time.sleep(0.01)
                continue
            active = _active_window(windows, active_id)
            phase = reference.get("fase")
            pending = int(reference.get("refuerzos_pendientes", 0))
            countries = _country_state(active)
            owned = [
                name
                for name in country_names
                if countries.get(name, {}).get("userid") == active_id
            ]
            if phase == "colocacion" and pending > 0:
                if not owned:
                    _fail("El jugador activo no recibió un país Qt")
                before = pending
                units = _connection(active).state_model.private_units
                options = [
                    name
                    for name in owned
                    if units.get("infanteria", 0)
                    + units.get(reader.continente(name) or "", 0)
                    > 0
                ]
                if not options:
                    app.processEvents()
                    time.sleep(0.01)
                    continue
                country = max(
                    options,
                    key=lambda name: (
                        sum(
                            neighbor not in owned
                            for neighbor in adjacency.get(name, ())
                        ),
                        int(countries[name].get("unidades", 0)),
                    ),
                )
                amount = min(
                    pending,
                    units.get("infanteria", 0)
                    + units.get(reader.continente(country) or "", 0),
                )
                _send_command(
                    app,
                    active,
                    {
                        "mensaje": "agregar_unidad",
                        "pais": country,
                        "tipo_unidad": "infanteria",
                        "cantidad": amount,
                    },
                    timeout,
                )
                _trace(f"placed reinforcement for {active_id}")

                def placement_done(before: int = before) -> bool:
                    snapshot = _snapshot(windows[0])
                    return (
                        int(snapshot.get("refuerzos_pendientes", 0)) < before
                        or snapshot.get("fase") != "colocacion"
                    )

                _wait_for(
                    app,
                    placement_done,
                    timeout,
                    "actualización de refuerzos Qt",
                )
                continue

            if phase != "acciones":
                time.sleep(0.01)
                continue

            if int(turn.get("num_ronda", 1)) >= MIN_COMBAT_ROUND:
                attack_options = [
                    (origin_name, target_name)
                    for origin_name in owned
                    for target_name in adjacency.get(origin_name, ())
                    if target_name not in owned
                    and int(countries.get(origin_name, {}).get("unidades", 0))
                    > int(countries.get(target_name, {}).get("unidades", 0))
                ]
                origin, target = (None, None)
                if attack_options:
                    origin, target = max(
                        attack_options,
                        key=lambda pair: (
                            int(countries[pair[0]]["unidades"])
                            - int(countries[pair[1]]["unidades"]),
                            pair[0],
                        ),
                    )
                if origin is not None and target is not None:
                    before_origin = dict(countries.get(origin, {}))
                    before_target = dict(countries.get(target, {}))
                    _send_command(
                        app,
                        active,
                        {
                            "mensaje": "atacar",
                            "origen": origin,
                            "destino": target,
                            "cantidad_unidades": min(
                                3, int(countries[origin]["unidades"]) - 1
                            ),
                        },
                        timeout,
                    )
                    _trace(f"attack {origin}->{target}")

                    def board_changed(
                        origin: str = origin,
                        target: str = target,
                        before_origin: dict[str, Any] = before_origin,
                        before_target: dict[str, Any] = before_target,
                    ) -> bool:
                        current = _country_state(windows[0])
                        return (
                            current.get(target, {}) != before_target
                            or current.get(origin, {}) != before_origin
                        )

                    _wait_for(
                        app,
                        board_changed,
                        timeout,
                        "resultado de ataque Qt",
                    )
                    if (
                        _country_state(windows[0]).get(target, {}).get("userid")
                        == active_id
                    ):
                        conquests += 1

            _send_command(app, active, {"mensaje": "finalizar_turno"}, timeout)
            turns += 1
            _trace(f"turn {turns} finished")
            _wait_convergence(app, windows, timeout)
            next_turn = _snapshot(windows[0]).get("turno") or {}
            if (
                int(next_turn.get("num_ronda", 1)) >= RECONNECT_ROUND
                and not reconnected
            ):
                replacement = _reconnect_client(
                    app,
                    port,
                    clients[1],
                    windows[1],
                    all_windows,
                    timeout,
                )
                windows[1] = replacement
                reconnected = True
                _trace("reconnected client 2")
                _wait_convergence(app, windows, timeout)
                _verify_situation(windows)
                situation_verified = True
                if args.output_dir is not None:
                    _capture_windows(
                        windows, args.output_dir, args.theme, args.rules_profile
                    )

        _wait_for(
            app,
            lambda: all(
                _snapshot(window).get("estado") == "Finalizado" for window in windows
            ),
            timeout,
            "estado final de las ventanas Qt",
        )
        winner = _snapshot(windows[0]).get("turno")
        _trace("final state observed")
        if conquests < 1 or not reconnected or not situation_verified:
            _fail("La partida debe verificar conquista, reconexión y carta visible")
        return {
            "status": "passed",
            "clients": len(windows),
            "theme": args.theme,
            "rules_profile": args.rules_profile,
            "situation_verified": situation_verified,
            "platform": app.platformName(),
            "map_rendered": args.render_map,
            "turns_played": turns,
            "conquests": conquests,
            "reconnected": reconnected,
            "final_states": [_snapshot(window).get("estado") for window in windows],
            "winner_turn": winner,
        }
    finally:
        _close_windows(app, all_windows)


def main() -> int:
    """Ejecuta la partida Qt y muestra evidencia JSON para CI.

    Returns:
        Código de salida cero sólo cuando la partida completa pasa.

    """
    args = _parse_args()
    if not args.visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    port = _free_port()
    server = _start_server(port, args.seed, args.theme, environment)
    _trace(f"server started on {port}")
    app = QApplication([])
    args.render_map = args.render_map or app.platformName() != "offscreen"
    try:
        _wait_for(
            app,
            lambda: server.poll() is not None or _server_listening(port),
            args.timeout,
            "inicio del servidor Qt",
        )
        if server.poll() is not None:
            output = server.stdout.read() if server.stdout is not None else ""
            _fail("El servidor terminó antes de escuchar:\n" + output)
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    WindowManager,
                    "show_battle_result_dialog",
                    _show_battle_non_blocking,
                )
            )
            if not args.render_map:
                stack.enter_context(
                    patch.object(
                        QtClientStateAdapter, "_sync_countries", _skip_country_render
                    )
                )
            stack.enter_context(
                patch.object(ClientTaskError, "run", _report_client_error)
            )
            stack.enter_context(
                patch.object(ClientTaskVictoria, "run", _report_victory)
            )
            result = _play_game(
                app, port, args, server_invitation(server, args.timeout)
            )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        result = {"status": "failed", "failure": str(error)}
    finally:
        _trace("stopping server")
        _stop_process(server)
        app.processEvents()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
