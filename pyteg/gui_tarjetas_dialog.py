"""Shim de compatibilidad: el diálogo vive ahora en `pyteg.gui.tarjetas`.

El código nuevo debe usar ``from pyteg.gui.tarjetas import TarjetasDialog``.
"""

from __future__ import annotations

from pyteg.gui.tarjetas import TarjetasDialog

__all__ = ["TarjetasDialog"]
