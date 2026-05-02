"""Shim de compatibilidad: la escena vive en `pyteg.gui.mapa.scene`."""

from __future__ import annotations

from pyteg.gui.mapa.scene import (
    CountrySelectionManager,
    QCustomGraphicsScene,
)

__all__ = [
    "CountrySelectionManager",
    "QCustomGraphicsScene",
]
