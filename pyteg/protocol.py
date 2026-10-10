"""Constantes y utilidades del contrato de red público."""

from __future__ import annotations

import hashlib

from pyteg.utils import get_resource_path

PROTOCOL_VERSION = "3"
SNAPSHOT_VERSION = 1


def map_hash_for_theme(theme: str) -> str:
    """Calcula el hash de los datos del mapa, sin el perfil de reglas.

    Returns:
        Hash SHA-256 hexadecimal del mapa y sus catálogos.

    """
    theme_dir = get_resource_path(f"themes/{theme}")
    digest = hashlib.sha256()
    for filename in (
        "paises.toml",
        "adyacencias.toml",
        "cartas.toml",
        "objetivos_secretos.toml",
    ):
        path = theme_dir / filename
        if not path.is_file():
            continue
        digest.update(filename.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
