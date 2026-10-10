"""Indicador flotante de unidades, anclado a la ficha del país."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGraphicsTextItem

from pyteg.gui.widgets.marker_layout import marker_obstacles, position_beside_marker

if TYPE_CHECKING:
    from PySide6.QtWidgets import (
        QGraphicsEllipseItem,
        QStyleOptionGraphicsItem,
        QWidget,
    )


class UnitDeltaIndicator(QGraphicsTextItem):
    """Muestra +N o -N con contraste y un desplazamiento local acotado."""

    def __init__(
        self, quantity: int, marker: QGraphicsEllipseItem, duration_ms: int
    ) -> None:
        """Prepara el texto y las animaciones bajo el mismo objeto gráfico."""
        super().__init__(f"{quantity:+d}", marker)
        self.document().setDocumentMargin(3)
        font = QFont("DejaVu Sans")
        font.setPixelSize(11)
        font.setBold(True)
        self.setFont(font)
        self.setDefaultTextColor(QColor("#FFFFFF"))
        self._background = QColor("#166534" if quantity > 0 else "#9F1D16")
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(50)
        self.setPos(
            position_beside_marker(
                marker,
                self.boundingRect().size(),
                marker_obstacles(marker, self),
                prefer_right=True,
                rise=duration_ms / 50 * 0.25,
            )
        )

        effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(effect)
        self.fade_animation = QPropertyAnimation(effect, b"opacity", effect)
        self.fade_animation.setDuration(duration_ms)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setKeyValueAt(0.5, 1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.fade_animation.finished.connect(self.movement_finished)
        self.fade_animation.finished.connect(self.deleteLater)

        self.movement_timer = QTimer(effect)
        self.movement_timer.setInterval(50)
        self.movement_timer.timeout.connect(self._move_up)

    def start(self) -> None:
        """Inicia el movimiento y el desvanecimiento sin bloquear Qt."""
        self.movement_timer.start()
        self.fade_animation.start()

    def stop(self) -> None:
        """Detiene ambos efectos antes de reemplazar el indicador."""
        self.movement_timer.stop()
        self.fade_animation.stop()

    def movement_finished(self) -> None:
        """Detiene el movimiento al terminar el desvanecimiento."""
        self.movement_timer.stop()

    def _move_up(self) -> None:
        # Un desplazamiento local no depende de la posición del país en el mapa.
        self.setY(self.y() - 0.25)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Dibuja un fondo de alto contraste detrás del cambio de unidades."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._background)
        painter.setPen(QPen(QColor("#FFF8EA"), 0.8))
        painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 3, 3)
        super().paint(painter, option, cast("QWidget", widget))
