"""Compatibilidad: importar `TarjetasDialog` desde el paquete `gui_tarjetas`.

El código nuevo debe usar ``from pyteg.gui_tarjetas import TarjetasDialog``.
"""

from __future__ import annotations

from pyteg.gui_tarjetas import TarjetasDialog

__all__ = ["TarjetasDialog"]
