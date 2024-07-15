from PySide6.QtGui import (
    QFont,
)
from PySide6.QtWidgets import (
    QGraphicsTextItem,
)


class Unidades(QGraphicsTextItem):

    def __init__(self, circulo_rect):
        super().__init__("0")
        self.setFont(QFont("Helvetica [Cronyx]", 14))

        # Centrar el texto dentro del elipse
        texto_rect = self.boundingRect()
        self.setPos(
            circulo_rect.center().x() - texto_rect.width() / 2,
            circulo_rect.center().y() - texto_rect.height() / 2,
        )
