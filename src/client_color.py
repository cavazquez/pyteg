from __future__ import annotations

from PySide6.QtGui import QColor


class Color(QColor):
    def __init__(self, r: int, g: int, b: int) -> None:
        super().__init__(r, g, b)
