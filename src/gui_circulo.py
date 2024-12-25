from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
)

from src.gui_unidades import Unidades


class Circulo(QGraphicsEllipseItem):
    def __init__(self, pos_x_abs, pos_y_abs):
        super().__init__(pos_x_abs, pos_y_abs, 30, 30)

        # Establecer el color del borde y del relleno del círculo
        self.setPen(QPen(Qt.blue))
        self.setBrush(QBrush(QColor(0, 255, 0)))  # Verde

        circulo_rect = self.boundingRect()

        self._center_text = Unidades(circulo_rect)
        self._center_text.setParentItem(self)

    def set_color(self, color):
        self.setBrush(QBrush(color))

    def set_unidades(self, cant):
        self._center_text.set_unidades(str(cant))
