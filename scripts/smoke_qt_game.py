"""Juega una partida corta con ventanas Qt y transporte TCP real.

El smoke usa el mapa clásico, tres instancias reales de ``Gui`` y el mismo
modelo Qt que usa el cliente distribuido. Configura e inicia la partida,
coloca refuerzos, conquista un país, reconecta una ventana durante la partida
y observa la victoria desde todos los clientes. El render de las 50 imágenes
del tablero se desacopla en el backend ``offscreen`` para mantener el recorrido
acotado; el smoke visual de conexión cubre la construcción del mapa. Los dados
se fijan sólo en el proceso servidor para que CI tenga un recorrido repetible.

Uso desde la raíz del repositorio::

    QT_QPA_PLATFORM=offscreen uv run python scripts/smoke_qt_game.py
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess  # noqa: S404 -- sólo inicia el servidor local del smoke
import sys
import time
import tomllib
import uuid
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

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT = 45.0
DEFAULT_SEED = 7
MIN_COMBAT_ROUND = 3
RECONNECT_AFTER_TURNS = 2
THEME = "classic"
CLIENT_COUNT = 3
VICTORY_TARGET = 18
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


def _connect_window(client: Client, port: int, theme: str, username: str) -> Gui:
    """Crea una ventana Qt de juego y la conecta al servidor local.

    Returns:
        Ventana Qt conectada al servidor.

    """
    window = Gui(client)
    window.hide()
    window.map_theme = theme
    dialog = VentanaConectar(window)
    window.ventana_conectar = dialog
    dialog.addr.setText("127.0.0.1")
    dialog.port.setText(str(port))
    dialog.username.setText(username)
    dialog.connect_to_server()
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
        description="Partida completa Qt con reconexión sobre el mapa de prueba.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout debe ser positivo")
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
        return len(boards) == len(windows) and len(set(boards)) == 1

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
) -> None:
    """Evita el coste del render de 50 imágenes en el backend offscreen."""


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
    """Reemplaza una ventana Qt desconectada usando el token de sesión.

    Returns:
        Nueva ventana Qt autenticada con la misma identidad.

    """
    _trace("reconnect start")
    user_id = client.userid()
    if user_id is None or not client.reconnect_token():
        _fail("El cliente Qt no tiene identidad o token para reconectar")
    connection = _connection(current_window)
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
    current_window.close()

    replacement = _connect_window(client, port, THEME, "QtGame2-Reconnected")
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


def _play_game(  # noqa: C901, PLR0912, PLR0914, PLR0915
    app: QApplication,
    port: int,
    timeout: float,
) -> dict[str, Any]:
    """Configura, juega y valida la partida con tres ventanas Qt.

    Returns:
        Evidencia serializable de victoria, turnos y reconexión.

    """
    _trace("creating clients")
    clients = [Client() for _ in range(CLIENT_COUNT)]
    all_windows: list[Gui] = []
    windows: list[Gui] = []
    for index, client in enumerate(clients, start=1):
        window = _connect_window(client, port, THEME, f"QtGame{index}")
        all_windows.append(window)
        windows.append(window)

    try:
        _wait_for(
            app,
            lambda: all(
                window.conexion is not None and window.client.userid() is not None
                for window in windows
            ),
            timeout,
            "handshake de las ventanas Qt",
        )
        _trace("handshake done")
        admin = windows[0]
        _send_command(
            app,
            admin,
            {
                "mensaje": "empezar",
                "segundos": 60,
                "paises_para_victoria": VICTORY_TARGET,
                "objetivos_secretos": False,
                "misiles_habilitados": False,
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
        country_names = tuple(_country_state(windows[0]))
        adjacency = _load_adjacency(THEME)

        turns = 0
        conquests = 0
        reconnected = False
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
                _send_command(
                    app,
                    active,
                    {
                        "mensaje": "agregar_unidad",
                        "pais": owned[0],
                        "tipo_unidad": "infanteria",
                        "cantidad": 1,
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
            if turns >= RECONNECT_AFTER_TURNS and not reconnected:
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
        return {
            "status": "passed",
            "clients": len(windows),
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
    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    port = _free_port()
    server = _start_server(port, args.seed, THEME, environment)
    _trace(f"server started on {port}")
    app = QApplication([])
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
        with (
            patch.object(
                WindowManager, "show_battle_result_dialog", _show_battle_non_blocking
            ),
            patch.object(QtClientStateAdapter, "_sync_countries", _skip_country_render),
            patch.object(ClientTaskError, "run", _report_client_error),
            patch.object(ClientTaskVictoria, "run", _report_victory),
        ):
            result = _play_game(app, port, args.timeout)
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
