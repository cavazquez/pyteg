"""Módulo para el widget gráfico que muestra la cantidad de unidades."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsTextItem

from pyteg.gui.color_contrast import contrast_ratio


class Unidades(QGraphicsTextItem):
    """Widget gráfico que muestra la cantidad de unidades en un círculo."""

    def __init__(self, circulo_rect: QRectF) -> None:
        """Inicializa el widget de unidades centrado en el rectángulo del círculo.

        Args:
            circulo_rect: Rectángulo del círculo donde se centrará el texto.

        """
        super().__init__("0")
        self._circulo_rect = QRectF(circulo_rect)
        self.document().setDocumentMargin(0)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        # Establecer color de texto blanco para mejor contraste
        self.setDefaultTextColor(Qt.GlobalColor.white)

        # Añadir efecto de sombra para mejorar la visibilidad
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setBlurRadius(2)
        self._shadow.setColor(Qt.GlobalColor.black)
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        self._fit_and_center()

    def _fit_and_center(self) -> None:
        """Ajusta el tamaño y vuelve a centrar al cambiar la cantidad."""
        font = QFont("sans-serif")
        font.setWeight(QFont.Weight.Bold)
        for size in range(12, 0, -1):
            font.setPixelSize(size)
            self.setFont(font)
            text_rect = self.boundingRect()
            if (
                text_rect.width() <= self._circulo_rect.width() - 3
                and text_rect.height() <= self._circulo_rect.height() - 1
            ):
                break
        self.setPos(self._circulo_rect.center() - self.boundingRect().center())

    def set_background_colors(self, colors: list[QColor]) -> None:
        """Elige texto negro o blanco según el contraste del relleno."""
        if not colors:
            return
        black, white = QColor("black"), QColor("white")
        ink = max(
            (black, white),
            key=lambda candidate: min(
                contrast_ratio(candidate, background) for background in colors
            ),
        )
        self.setDefaultTextColor(ink)
        self._shadow.setColor(white if ink == black else black)

    def set_unidades(self, text: str) -> None:
        """Establece el texto que muestra la cantidad de unidades.

        Args:
            text: Texto a mostrar (normalmente un número como string).

        """
        self.setPlainText(text)
        self._fit_and_center()

    def get_unidades(self) -> int:
        """Retorna la cantidad de unidades como entero.

        Returns:
            Cantidad de unidades como entero.

        """
        try:
            return int(self.toPlainText())
        except ValueError:
            return 0
