"""Verifica que el sdist contenga los recursos necesarios para PyTeg."""

from __future__ import annotations

import argparse
import sys
import tarfile
from pathlib import Path

REQUIRED_FILES = (
    "pyproject.toml",
    "themes/classic/paises.toml",
    "themes/classic/cartas.toml",
    "themes/classic/adyacencias.toml",
    "themes/classic/objetivos_secretos.toml",
    "themes/classic/reglas.toml",
    "themes/test/paises.toml",
    "themes/test/adyacencias.toml",
    "themes/revancha/paises.toml",
    "themes/revancha/cartas.toml",
    "themes/revancha/adyacencias.toml",
    "themes/revancha/objetivos_secretos.toml",
    "themes/revancha/reglas.toml",
    "themes/revancha/countries/Argentina.svg",
    "themes/revancha/cards/Avion.svg",
    "themes/revancha/geometry/revancha-shell.svg",
    "themes/revancha/geometry/revancha-borders.svg",
    "themes/revancha/geometry/revancha-manifest.json",
    "themes/revancha/geometry/generate_revancha_map.py",
    "themes/classic/argentina.svg",
    "themes/classic/geometry/asia-manifest.json",
    "themes/classic/geometry/asia-partition.png",
    "themes/classic/geometry/asia-block.png",
    "themes/classic/geometry/asia-shell.svg",
    "themes/classic/geometry/asia-borders.svg",
    "icons/conectar.png",
    "sounds/attack.wav",
    "locales/en/LC_MESSAGES/pyteg.po",
    "locales/es/LC_MESSAGES/pyteg.po",
)


def parse_args() -> argparse.Namespace:
    """Parsea el sdist a verificar.

    Returns:
        Argumentos de línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Verifica los recursos incluidos en un sdist de PyTeg.",
    )
    parser.add_argument("sdist", type=Path)
    return parser.parse_args()


def _relative_files(archive: tarfile.TarFile) -> set[str]:
    """Obtiene archivos sin el directorio raíz versionado del sdist.

    Returns:
        Rutas relativas de los archivos del archivo fuente.

    """
    relative_files: set[str] = set()
    for member in archive.getmembers():
        if not member.isfile() or "/" not in member.name:
            continue
        _root, relative = member.name.split("/", 1)
        relative_files.add(relative)
    return relative_files


def main() -> int:
    """Devuelve un código distinto de cero si falta un recurso.

    Returns:
        Código de salida del verificador.

    """
    sdist = parse_args().sdist
    if not sdist.is_file():
        print(f"Sdist no encontrado: {sdist}", file=sys.stderr)
        return 2

    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            files = _relative_files(archive)
    except (tarfile.TarError, OSError) as error:
        print(f"Sdist inválido: {error}", file=sys.stderr)
        return 2

    missing = [path for path in REQUIRED_FILES if path not in files]
    if missing:
        print("Faltan recursos en el sdist:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 1

    print(f"Sdist verificado: {sdist} ({len(files)} archivos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
