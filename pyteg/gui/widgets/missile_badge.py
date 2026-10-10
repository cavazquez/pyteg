"""Marcador de misiles con un icono vectorial independiente de las fuentes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

from pyteg.gui.widgets.marker_layout import position_beside_marker
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtCore import QRectF
    from PySide6.QtWidgets import (
        QGraphicsEllipseItem,
        QStyleOptionGraphicsItem,
        QWidget,
    )


class MissileBadge(QGraphicsRectItem):
    """Placa compacta con un misil dibujado y su cantidad."""

    def __init__(self) -> None:
        """Crea el icono y el contador como hijos de la placa."""
        super().__init__()
        self.setBrush(QBrush(QColor("#9F1D16")))
        self.setPen(QPen(QColor("#FFE08A"), 1))
        self.setZValue(20)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.icon = QGraphicsSvgItem(str(get_resource_path("icons/missile.svg")), self)
        self.icon.setPos(3, 2)
        self.icon.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.count_text = QGraphicsTextItem(self)
        self.count_text.document().setDocumentMargin(0)
        font = QFont("DejaVu Sans")
        font.setPixelSize(9)
        font.setBold(True)
        self.count_text.setFont(font)
        self.count_text.setDefaultTextColor(QColor("#FFFFFF"))
        self.count_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def set_count(self, quantity: int) -> None:
        """Actualiza la cantidad y ajusta el ancho sin escalar el icono."""
        self.count_text.setPlainText(str(quantity))
        bounds = self.count_text.boundingRect()
        height = max(16.0, bounds.height() + 4)
        self.setRect(0, 0, 21 + bounds.width(), height)
        self.count_text.setPos(18, (height - bounds.height()) / 2)
        self.icon.setY((height - self.icon.boundingRect().height()) / 2)

    def place_next_to(
        self, marker: QGraphicsEllipseItem, obstacles: Iterable[QRectF]
    ) -> None:
        """Elige un lado de la ficha que deje visibles nombres y otras fichas."""
        self.setParentItem(marker)
        self.setPos(position_beside_marker(marker, self.rect().size(), obstacles))

    def paint(
        self,
        painter: QPainter,
        _option: QStyleOptionGraphicsItem,
        _widget: QWidget | None = None,
    ) -> None:
        """Dibuja un fondo con contraste y esquinas redondeadas."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), 3, 3)
