"""Verifica que el wheel contenga los recursos necesarios para ejecutar PyTeg."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zipfile import ZipFile

REQUIRED_FILES = (
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
    "themes/classic/argentina.svg",
    "icons/conectar.png",
    "icons/atacar.png",
    "sounds/attack.wav",
    "sounds/dice.wav",
    "locales/en/LC_MESSAGES/pyteg.mo",
    "locales/es/LC_MESSAGES/pyteg.mo",
)


def parse_args() -> argparse.Namespace:
    """Parsea el wheel a verificar.

    Returns:
        Argumentos de línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Verifica los recursos incluidos en un wheel de PyTeg.",
    )
    parser.add_argument("wheel", type=Path)
    return parser.parse_args()


def main() -> int:
    """Devuelve un código distinto de cero si falta un recurso.

    Returns:
        Código de salida del verificador.

    """
    wheel = parse_args().wheel
    if not wheel.is_file():
        print(f"Wheel no encontrado: {wheel}", file=sys.stderr)
        return 2

    with ZipFile(wheel) as archive:
        files = set(archive.namelist())

    missing = [path for path in REQUIRED_FILES if path not in files]
    if missing:
        print("Faltan recursos en el wheel:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 1

    print(f"Wheel verificado: {wheel} ({len(files)} entradas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
