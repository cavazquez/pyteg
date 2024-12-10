from PySide6.QtGui import QColor


class Color(QColor):
    def __init__(self, r, g, b):
        super().__init__(r, g, b)
