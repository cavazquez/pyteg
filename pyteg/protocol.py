"""Constantes y utilidades del contrato de red público."""

from __future__ import annotations

import hashlib

from pyteg.utils import get_resource_path

PROTOCOL_VERSION = "1"
SNAPSHOT_VERSION = 1


def map_hash_for_theme(theme: str) -> str:
    """Calcula el hash de las dos fuentes públicas del mapa.

    Returns:
        Hash SHA-256 hexadecimal de los metadatos públicos del tema.

    """
    theme_dir = get_resource_path(f"themes/{theme}")
    digest = hashlib.sha256()
    for filename in ("paises.toml", "adyacencias.toml"):
        path = theme_dir / filename
        digest.update(filename.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
