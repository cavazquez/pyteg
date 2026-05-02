"""Shim de compatibilidad: la escena vive en `pyteg.gui.mapa.scene`."""

from __future__ import annotations

from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.gui.mapa.selection_manager import CountrySelectionManager

__all__ = [
    "CountrySelectionManager",
    "QCustomGraphicsScene",
]
