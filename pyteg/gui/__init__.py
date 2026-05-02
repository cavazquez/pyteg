"""Paquete principal de la interfaz gráfica del cliente PyTeg.

`from pyteg.gui import Gui` sigue funcionando: la clase vive ahora en
:mod:`pyteg.gui.main_window`.
"""

from __future__ import annotations

from pyteg.gui.main_window import Gui

__all__ = ["Gui"]
