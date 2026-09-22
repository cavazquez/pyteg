"""Comprueba varias ventanas Qt contra un servidor PyTeg real.

El smoke no juega una partida completa: verifica la capa que el simulador
headless no puede cubrir, es decir, que varias ventanas ``Gui`` reciban el
handshake y que una de ellas pueda recuperar la sesión con su token.

Uso desde la raíz del repositorio::

    QT_QPA_PLATFORM=offscreen uv run python scripts/smoke_qt_multiclient.py
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess  # noqa: S404 -- sólo inicia el servidor local del smoke
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.conexion.connection import ConnectionClient
from pyteg.gui import Gui
from pyteg.gui.dialogs.conectar import VentanaConectar

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIENTS = 3
DEFAULT_TIMEOUT = 15.0
MIN_CLIENTS = 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke Qt multicliente con reconexión autenticada.",
    )
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--theme", choices=("classic", "test"), default="classic")
    args = parser.parse_args()
    if args.clients < MIN_CLIENTS:
        parser.error("--clients debe ser al menos 2")
    if args.timeout <= 0:
        parser.error("--timeout debe ser positivo")
    return args


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _server_listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def _wait_for(
    app: QApplication,
    predicate: Callable[[], bool],
    timeout: float,
    description: str,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.05)
    app.processEvents()
    if not predicate():
        message = f"Timeout esperando {description}"
        raise RuntimeError(message)


def _connect_window(client: Client, port: int, theme: str, username: str) -> Gui:
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


def _start_server(
    port: int, theme: str, environment: dict[str, str]
) -> subprocess.Popen[str]:
    return subprocess.Popen(  # noqa: S603 -- argumentos estáticos del smoke
        [
            sys.executable,
            "-m",
            "pyteg.server.app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--theme",
            theme,
            "--quiet",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _server_output(server: subprocess.Popen[str]) -> str:
    if server.stdout is None:
        return ""
    output = server.stdout.read()
    if not isinstance(output, str):
        msg = "Expected text output from the subprocess"
        raise TypeError(msg)
    return output


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _close_windows(app: QApplication, windows: list[Gui]) -> None:
    for window in windows:
        connection = window.conexion
        if isinstance(connection, ConnectionClient):
            connection.desconectar()
        window.close()
    app.processEvents()


def _client_userid(client: Client) -> int:
    user_id = client.userid()
    if user_id is None:
        message = "El cliente no tiene userid"
        raise RuntimeError(message)
    return int(user_id)


def main() -> int:
    """Ejecuta el smoke y devuelve cero si conserva la identidad.

    Returns:
        ``0`` cuando todos los clientes se conectan y uno se recupera.

    Raises:
        RuntimeError: Si falla el servidor, el handshake o la reconexión.
        TypeError: Si la ventana no tiene una conexión Qt.

    """
    args = _parse_args()
    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    port = _free_port()
    server = _start_server(port, args.theme, environment)
    app = QApplication([])
    windows: list[Gui] = []
    clients: list[Client] = []

    try:
        _wait_for(
            app,
            lambda: server.poll() is not None or _server_listening(port),
            args.timeout,
            "inicio del servidor",
        )
        if server.poll() is not None:
            raise RuntimeError(
                "El servidor terminó antes de escuchar:\n" + _server_output(server)
            )

        for index in range(args.clients):
            client = Client()
            clients.append(client)
            windows.append(
                _connect_window(client, port, args.theme, f"QtSmoke{index + 1}")
            )

        _wait_for(
            app,
            lambda: (
                all(client.userid() is not None for client in clients)
                and all(
                    window.conexion is not None and window.conexion.esta_conectado()
                    for window in windows
                )
            ),
            args.timeout,
            "handshake de los clientes Qt",
        )
        user_ids = [_client_userid(client) for client in clients]

        reconnect_client = clients[1]
        reconnect_user_id = _client_userid(reconnect_client)
        if not reconnect_client.reconnect_token():
            message = "El cliente no recibió token de sesión"
            raise RuntimeError(message)
        connection = windows[1].conexion
        if not isinstance(connection, ConnectionClient):
            message = "El cliente no tiene conexión Qt"
            raise TypeError(message)
        connection.desconectar()
        _wait_for(
            app,
            lambda: windows[1].conexion is None,
            args.timeout,
            "desconexión del cliente Qt",
        )

        replacement = _connect_window(
            reconnect_client, port, args.theme, "QtSmoke2-Reconnected"
        )
        windows.append(replacement)
        _wait_for(
            app,
            lambda: (
                replacement.conexion is not None
                and replacement.conexion.esta_conectado()
                and reconnect_client.userid() == reconnect_user_id
            ),
            args.timeout,
            "reconexión autenticada del cliente Qt",
        )
        print(
            f"Qt smoke OK: {len(user_ids)} clientes conectados ({user_ids}); "
            f"reconexión conservó userid {reconnect_user_id}"
        )
        return 0
    finally:
        _close_windows(app, windows)
        _stop_process(server)


if __name__ == "__main__":
    raise SystemExit(main())
