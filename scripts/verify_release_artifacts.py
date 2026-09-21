"""Verifica los cuatro paquetes que debe adjuntar un release de PyTeg."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PLATFORMS = (
    ("linux", "x86_64", ".tar.gz"),
    ("windows", "x86_64", ".zip"),
    ("macos", "x86_64", ".tar.gz"),
    ("macos", "arm64", ".tar.gz"),
)


def parse_args() -> argparse.Namespace:
    """Parsea el directorio y la versión de los artefactos.

    Returns:
        Argumentos de línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Verifica los artefactos multiplataforma de un release.",
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def expected_artifacts(directory: Path, version: str) -> list[Path]:
    """Construye los cuatro nombres canónicos esperados.

    Returns:
        Rutas de los cuatro paquetes del release.

    """
    return [
        directory / f"pyteg-{version}-{platform}-{arch}{suffix}"
        for platform, arch, suffix in PLATFORMS
    ]


def main() -> int:
    """Falla si falta un paquete esperado.

    Returns:
        Código de salida del verificador.

    """
    args = parse_args()
    artifacts = expected_artifacts(args.directory, args.version)
    missing = [path for path in artifacts if not path.is_file()]
    if missing:
        print("Faltan artefactos del release:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 1

    print(f"Release verificado: {len(artifacts)} artefactos para {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
