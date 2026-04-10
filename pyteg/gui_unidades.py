"""Módulo para el widget gráfico que muestra la cantidad de unidades."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsTextItem


class Unidades(QGraphicsTextItem):
    """Widget gráfico que muestra la cantidad de unidades en un círculo."""

    def __init__(self, circulo_rect: QRectF) -> None:
        """Inicializa el widget de unidades centrado en el rectángulo del círculo.

        Args:
            circulo_rect: Rectángulo del círculo donde se centrará el texto.

        """
        super().__init__("0")
        font = QFont("Helvetica [Cronyx]", 8, QFont.Weight.Bold)
        self.setFont(font)

        # Establecer color de texto blanco para mejor contraste
        self.setDefaultTextColor(Qt.GlobalColor.white)

        # Añadir efecto de sombra para mejorar la visibilidad
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(3)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)

        # Centrar el texto dentro del elipse
        texto_rect = self.boundingRect()
        self.setPos(
            circulo_rect.center().x() - texto_rect.width() / 2,
            circulo_rect.center().y() - texto_rect.height() / 2,
        )

    def set_unidades(self, text: str) -> None:
        """Establece el texto que muestra la cantidad de unidades.

        Args:
            text: Texto a mostrar (normalmente un número como string).

        """
        self.setPlainText(text)

    def get_unidades(self) -> int:
        """Retorna la cantidad de unidades como entero.

        Returns:
            Cantidad de unidades como entero.

        """
        try:
            return int(self.toPlainText())
        except ValueError:
            return 0
