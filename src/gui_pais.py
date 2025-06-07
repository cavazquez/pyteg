from PySide6.QtGui import (
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
)

from src.gui_circulo import Circulo


class Pais(QGraphicsPixmapItem):
    def __init__(self, path, pais, pos):
        super().__init__(QPixmap(path))
        self._nombre, self._continente = pais
        self._x, self._y, self._army_x, self._army_y = pos
        self.setPos(self._x, self._y)
        self._circle = None
        self._center_text = None

        self.cargar_circulo()

    def cargar_circulo(self):
        pos_x_abs = self._army_x
        pos_y_abs = self._army_y
        # (x, y)
        self._circle = Circulo(pos_x_abs, pos_y_abs)
        self._circle.setParentItem(self)

    def nombre(self):
        return self._nombre

    def set_color(self, color):
        if color:
            self._circle.set_color(color)

    def set_unidades(self, cant):
        self._circle.set_unidades(cant)
