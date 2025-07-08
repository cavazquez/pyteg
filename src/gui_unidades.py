from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QFont,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsTextItem,
)


class Unidades(QGraphicsTextItem):
    def __init__(self, circulo_rect):
        super().__init__("0")
        font = QFont("Helvetica [Cronyx]", 14, QFont.Bold)
        self.setFont(font)

        # Establecer color de texto blanco para mejor contraste
        self.setDefaultTextColor(Qt.white)

        # Añadir efecto de sombra para mejorar la visibilidad
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(3)
        shadow.setColor(Qt.black)
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)

        # Centrar el texto dentro del elipse
        texto_rect = self.boundingRect()
        self.setPos(
            circulo_rect.center().x() - texto_rect.width() / 2,
            circulo_rect.center().y() - texto_rect.height() / 2,
        )

    def set_unidades(self, text):
        self.setPlainText(text)
