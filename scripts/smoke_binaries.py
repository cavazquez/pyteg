"""Comprueba que los binarios Nuitka carguen ambos temas fuera del checkout."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess  # noqa: S404 -- sólo ejecuta los binarios recién construidos
import tempfile
import time
from contextlib import suppress
from pathlib import Path

_STARTUP_SECONDS = 3.0


def _stop(process: subprocess.Popen[str]) -> None:
    """Cierra el launcher Nuitka y su proceso hijo antes de borrar los logs."""
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(  # noqa: S603 -- PID del proceso creado por la prueba.
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],  # noqa: S607
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
    elif hasattr(os, "killpg") and hasattr(signal, "SIGKILL"):
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    try:
        process.wait(timeout=5)
    finally:
        if process.stdout is not None:
            process.stdout.close()


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
        start_new_session=os.name != "nt",
    )
    try:
        time.sleep(_STARTUP_SECONDS)
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            message = f"El servidor Nuitka terminó al cargar {theme}: {output}"
            raise RuntimeError(message)
    finally:
        _stop(process)


def _run_client(client: Path, theme: str, cwd: Path, env: dict[str, str]) -> None:
    process = subprocess.Popen(  # noqa: S603 -- ruta validada por el workflow
        [str(client), "--quiet", "--theme", theme],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=os.name != "nt",
    )
    try:
        time.sleep(_STARTUP_SECONDS)
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            message = f"El cliente Nuitka terminó al cargar {theme}: {output}"
            raise RuntimeError(message)
    finally:
        _stop(process)


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
    clean_env.pop("PYTEG_VERSION", None)
    clean_env["QT_QPA_PLATFORM"] = "offscreen"
    server = args.server.resolve()
    client = args.client.resolve()
    with tempfile.TemporaryDirectory(prefix="pyteg-binary-smoke-") as temp_dir:
        clean_cwd = Path(temp_dir)
        for theme in ("classic", "revancha"):
            _run_server(server, theme, clean_cwd, clean_env)
            _run_client(client, theme, clean_cwd, clean_env)
    print("Binarios Nuitka verificados para classic y revancha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
