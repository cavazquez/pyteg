"""Módulo para el widget gráfico de círculo que muestra unidades."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem

from src.gui_unidades import Unidades


class Circulo(QGraphicsEllipseItem):
    """Círculo gráfico que muestra el color y cantidad de unidades de un país."""

    def __init__(self, pos_x_abs: float, pos_y_abs: float) -> None:
        """Inicializa el círculo en la posición especificada.

        Args:
            pos_x_abs: Posición X absoluta.
            pos_y_abs: Posición Y absoluta.

        """
        super().__init__(pos_x_abs, pos_y_abs, 16, 16)

        # Establecer el color del borde y del relleno del círculo
        self.setPen(QPen(Qt.GlobalColor.blue))
        self.setBrush(QBrush(QColor(0, 255, 0)))  # Verde

        circulo_rect = self.boundingRect()

        self._center_text = Unidades(circulo_rect)
        self._center_text.setParentItem(self)

    def set_color(self, color: QColor | str | None) -> None:
        """Establece el color del círculo.

        Args:
            color: Color a establecer (QColor, string hexadecimal o None).

        """
        if color is None:
            return
        if isinstance(color, QColor):
            self.setBrush(QBrush(color))
            return

        try:
            qcolor = QColor(color)
            if qcolor.isValid():
                self.setBrush(QBrush(qcolor))
            else:
                print(f"Color no válido: {color}")
        except (ValueError, TypeError) as exc:
            print(f"Error al establecer el color: {exc}")

    def set_unidades(self, cant: int | str) -> None:
        """Establece la cantidad de unidades a mostrar.

        Args:
            cant: Cantidad de unidades (int o string).

        """
        self._center_text.set_unidades(str(cant))

    def get_unidades(self) -> int:
        """Retorna la cantidad de unidades como entero.

        Returns:
            Cantidad de unidades como entero.

        """
        return int(self._center_text.get_unidades())
