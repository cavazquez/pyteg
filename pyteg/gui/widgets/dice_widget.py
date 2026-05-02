"""Widget de un dado con animación para resultados de batalla."""

from __future__ import annotations

import secrets

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget


class DiceWidget(QWidget):
    """Widget que representa un dado con animación."""

    def __init__(self, final_value: int = 1, parent: QWidget | None = None) -> None:
        """Inicializa el widget de dado.

        Args:
            final_value: Valor final que mostrará el dado (1-6).
            parent: Widget padre (opcional).

        """
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._current_value = 1
        self._final_value = final_value
        self._is_animating = False
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_step)

    def start_animation(self, duration_ms: int = 2000) -> None:
        """Inicia la animación del dado."""
        self._is_animating = True
        self._animation_timer.start(100)  # Cambiar valor cada 100ms

        # Detener animación después del tiempo especificado
        QTimer.singleShot(duration_ms, self._stop_animation)

    def _animate_step(self) -> None:
        """Paso de animación - cambia el valor del dado aleatoriamente."""
        if self._is_animating:
            self._current_value = secrets.randbelow(6) + 1
            self.update()

    def _stop_animation(self) -> None:
        """Detiene la animación y muestra el valor final."""
        self._is_animating = False
        self._animation_timer.stop()
        self._current_value = self._final_value
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Dibuja el dado con su valor actual."""
        del event  # Unused parameter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar fondo del dado
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(rect, 8, 8)

        # Dibujar puntos según el valor
        self._draw_dice_dots(painter, rect, self._current_value)

    def _draw_dice_dots(self, painter: QPainter, rect: QRect, value: int) -> None:
        """Dibuja los puntos del dado según su valor."""
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(Qt.PenStyle.NoPen)

        dot_size = 6
        center_x = rect.center().x()
        center_y = rect.center().y()
        offset = 12

        # Posiciones de los puntos
        positions = {
            1: [(center_x, center_y)],
            2: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y + offset),
            ],
            3: [
                (center_x - offset, center_y - offset),
                (center_x, center_y),
                (center_x + offset, center_y + offset),
            ],
            4: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
            5: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x, center_y),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
            6: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x - offset, center_y),
                (center_x + offset, center_y),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
        }

        # Dibujar los puntos
        for x, y in positions.get(value, []):
            painter.drawEllipse(
                x - dot_size // 2, y - dot_size // 2, dot_size, dot_size
            )
