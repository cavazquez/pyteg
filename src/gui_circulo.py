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
        super().__init__(pos_x_abs, pos_y_abs, 16, 16)

        # Establecer el color del borde y del relleno del círculo
        self.setPen(QPen(Qt.blue))
        self.setBrush(QBrush(QColor(0, 255, 0)))  # Verde

        circulo_rect = self.boundingRect()

        self._center_text = Unidades(circulo_rect)
        self._center_text.setParentItem(self)

    def set_color(self, color):
        if color:
            if isinstance(color, QColor):
                self.setBrush(QBrush(color))
            else:
                # Si el color no es un QColor, intentar convertirlo
                try:
                    qcolor = QColor(color)
                    if qcolor.isValid():
                        self.setBrush(QBrush(qcolor))
                    else:
                        print(f"Color no válido: {color}")
                except (ValueError, TypeError) as e:
                    print(f"Error al establecer el color: {e}")

    def set_unidades(self, cant):
        self._center_text.set_unidades(str(cant))

    def get_unidades(self):
        """Retorna la cantidad de unidades como entero."""
        return self._center_text.get_unidades()
