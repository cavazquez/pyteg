"""Arranca servidor y cliente desde un wheel extraído fuera del checkout."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess  # noqa: S404
import sys
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

_STARTUP_TIMEOUT = 8.0
_CLIENT_RUNTIME = 2.0


def parse_args() -> argparse.Namespace:
    """Parsea el wheel a probar.

    Returns:
        Argumentos de línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Arranca servidor y cliente desde un wheel aislado.",
    )
    parser.add_argument("wheel", type=Path)
    return parser.parse_args()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _environment(root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return environment


def _process_output(process: subprocess.Popen[str]) -> str:
    if process.stdout is None:
        return ""
    return process.stdout.read()


def _stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def _wait_for_server(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + _STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = _process_output(process)
            message = f"El servidor terminó antes de escuchar:\n{output}"
            raise RuntimeError(message)
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    message = "El servidor no abrió el puerto dentro del tiempo esperado"
    raise RuntimeError(message)


def _run_server(root: Path, cwd: Path, theme: str) -> None:
    port = _free_port()
    process = subprocess.Popen(  # noqa: S603
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
        cwd=cwd,
        env=_environment(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server(process, port)
        print(f"Servidor del wheel inició correctamente con tema {theme}")
    finally:
        _stop(process)


def _run_client(root: Path, cwd: Path) -> None:
    process = subprocess.Popen(
        [sys.executable, "-m", "pyteg.client.run", "--quiet"],
        cwd=cwd,
        env=_environment(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(_CLIENT_RUNTIME)
        if process.poll() is not None:
            output = _process_output(process)
            message = f"El cliente terminó al iniciar:\n{output}"
            raise RuntimeError(message)
        print("Cliente Qt offscreen del wheel inició correctamente")
    finally:
        _stop(process)


def main() -> int:
    """Extrae el wheel y ejecuta los dos smoke tests fuera del checkout.

    Returns:
        Código de salida del smoke test.

    """
    wheel = parse_args().wheel
    if not wheel.is_file():
        print(f"Wheel no encontrado: {wheel}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="pyteg-wheel-smoke-") as temp_dir:
        root = Path(temp_dir) / "installed"
        cwd = Path(temp_dir) / "empty"
        root.mkdir()
        cwd.mkdir()
        with ZipFile(wheel) as archive:
            archive.extractall(root)
        for theme in ("classic", "revancha"):
            _run_server(root, cwd, theme)
        _run_client(root, cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
