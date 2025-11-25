"""Módulo para manejo de colores del cliente."""

from __future__ import annotations

from PySide6.QtGui import QColor


class Color(QColor):
    """Clase para representar colores RGB."""

    def __init__(self, r: int, g: int, b: int) -> None:
        """Inicializa un color con valores RGB.

        Args:
            r: Componente rojo (0-255).
            g: Componente verde (0-255).
            b: Componente azul (0-255).

        """
        super().__init__(r, g, b)
