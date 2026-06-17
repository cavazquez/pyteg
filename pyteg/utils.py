"""Utilidades generales del proyecto PyTeg."""

from __future__ import annotations

from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta a un recurso del proyecto.

    Returns:
        Ruta absoluta al recurso.

    """
    return BASE_DIR / relative_path
