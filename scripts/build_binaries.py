"""Construye los binarios standalone de servidor y cliente con Nuitka."""

from __future__ import annotations

import argparse
import os
import subprocess  # noqa: S404
import sys
from pathlib import Path

SERVER_ENTRY = Path("pyteg/server/app.py")
CLIENT_ENTRY = Path("pyteg/client/run.py")
RESOURCE_DIRS = ("themes", "locales", "icons", "sounds")


def parse_args() -> argparse.Namespace:
    """Parsea la versión y el directorio de salida.

    Returns:
        Argumentos de línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Construye los ejecutables standalone de PyTeg.",
    )
    parser.add_argument("--version", required=True, help="Versión sin prefijo v")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Directorio donde se escriben los binarios",
    )
    return parser.parse_args()


def _nuitka_command(
    entry: Path,
    output: Path,
    *,
    disable_console: bool,
    output_dir: Path,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--standalone",
        f"--output-filename={output.name}",
        f"--output-dir={output_dir}",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
    ]
    if disable_console:
        command.append("--disable-console")
    command.extend(
        f"--include-data-dir={directory}={directory}" for directory in RESOURCE_DIRS
    )
    command.append(str(entry))
    return command


def _build_one(
    entry: Path,
    output: Path,
    *,
    disable_console: bool,
    output_dir: Path,
    version: str,
) -> None:
    command = _nuitka_command(
        entry,
        output,
        disable_console=disable_console,
        output_dir=output_dir,
    )
    environment = os.environ | {"PYTEG_VERSION": version}
    subprocess.run(command, check=True, env=environment)  # noqa: S603


def main() -> int:
    """Comprueba las entradas y construye ambos ejecutables.

    Returns:
        Código de salida del proceso.

    """
    args = parse_args()
    entries = (SERVER_ENTRY, CLIENT_ENTRY)
    missing = [entry for entry in entries if not entry.is_file()]
    if missing:
        for entry in missing:
            print(f"Entrada Nuitka no encontrada: {entry}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".exe" if os.name == "nt" else ""
    _build_one(
        SERVER_ENTRY,
        args.output_dir / f"pyteg-server-{args.version}{suffix}",
        disable_console=False,
        output_dir=args.output_dir,
        version=args.version,
    )
    _build_one(
        CLIENT_ENTRY,
        args.output_dir / f"pyteg-client-{args.version}{suffix}",
        disable_console=True,
        output_dir=args.output_dir,
        version=args.version,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
