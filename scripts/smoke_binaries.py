"""Comprueba que los binarios Nuitka carguen ambos temas fuera del checkout."""

from __future__ import annotations

import argparse
import os
import subprocess  # noqa: S404 -- sólo ejecuta los binarios recién construidos
import tempfile
import time
from pathlib import Path

_STARTUP_SECONDS = 1.5


def parse_args() -> argparse.Namespace:
    """Parsea las rutas de los ejecutables compilados.

    Returns:
        Argumentos del smoke test.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--client", type=Path, required=True)
    return parser.parse_args()


def _run_server(server: Path, theme: str, cwd: Path, env: dict[str, str]) -> None:
    process = subprocess.Popen(  # noqa: S603 -- ruta validada por el workflow
        [
            str(server),
            "--host",
            "127.0.0.1",
            "--port",
            "0",
            "--theme",
            theme,
            "--quiet",
        ],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(_STARTUP_SECONDS)
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            message = f"El servidor Nuitka terminó al cargar {theme}: {output}"
            raise RuntimeError(message)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _run_client(client: Path, cwd: Path, env: dict[str, str]) -> None:
    process = subprocess.Popen(  # noqa: S603 -- ruta validada por el workflow
        [str(client), "--quiet"],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(_STARTUP_SECONDS)
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            message = f"El cliente Nuitka terminó al iniciar: {output}"
            raise RuntimeError(message)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main() -> int:
    """Ejecuta el smoke de servidor para ambos temas y del cliente.

    Returns:
        Código de salida del smoke test.

    """
    args = parse_args()
    for executable in (args.server, args.client):
        if not executable.is_file():
            print(f"Binario no encontrado: {executable}")
            return 2

    clean_env = os.environ.copy()
    clean_env.pop("PYTHONHOME", None)
    clean_env.pop("PYTHONPATH", None)
    clean_env["PYTEG_VERSION"] = "smoke"
    clean_env["QT_QPA_PLATFORM"] = "offscreen"
    server = args.server.resolve()
    client = args.client.resolve()
    with tempfile.TemporaryDirectory(prefix="pyteg-binary-smoke-") as temp_dir:
        clean_cwd = Path(temp_dir)
        for theme in ("classic", "revancha"):
            _run_server(server, theme, clean_cwd, clean_env)
        _run_client(client, clean_cwd, clean_env)
    print("Binarios Nuitka verificados para classic y revancha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
