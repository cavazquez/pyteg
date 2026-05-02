"""Efectos visuales de batalla y misiles sobre un país del mapa."""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsOpacityEffect,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
)

from pyteg.config import TITILATION_MAX_INTENSITY
from pyteg.logger import get_logger

_LOG = get_logger("gui.pais.fx")


class PaisBattleFxMixin:
    """Titilación, pérdidas flotantes e indicador de misiles (país)."""

    _nombre: str
    _army_x: float
    _army_y: float
    _misiles_text: QGraphicsTextItem | None
    _cantidad_misiles: int
    _titilacion_timer: QTimer | None
    _titilacion_effect: QGraphicsColorizeEffect | None
    _titilacion_intensidad: float
    _titilacion_direccion: int
    _perdida_flotante: QGraphicsTextItem | None
    _opacity_animation: QPropertyAnimation | None
    _movimiento_timer: QTimer | None

    def actualizar_misiles(self, cantidad: int) -> None:
        """Actualiza el indicador visual de misiles en el país."""
        try:
            self._cantidad_misiles = cantidad

            if cantidad == 0:
                if self._misiles_text:
                    if self._misiles_text.scene():
                        self._misiles_text.scene().removeItem(self._misiles_text)
                    self._misiles_text = None
                return

            if self._misiles_text:
                self._misiles_text.setPlainText(f"🚀{cantidad}")
            else:
                self._misiles_text = QGraphicsTextItem(f"🚀{cantidad}")
                self._misiles_text.setParentItem(cast("QGraphicsPixmapItem", self))

                font = QFont("Arial", 12, QFont.Weight.Bold)
                self._misiles_text.setFont(font)
                self._misiles_text.setDefaultTextColor(QColor(255, 50, 50))

                pos_x = self._army_x - 15
                pos_y = self._army_y - 45
                self._misiles_text.setPos(pos_x, pos_y)

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error actualizando misiles en %s: %s", self._nombre, e)

    def iniciar_titilacion_batalla(self) -> None:
        """Inicia el efecto de titilación durante una batalla."""
        try:
            self.detener_titilacion_batalla()

            self._titilacion_effect = QGraphicsColorizeEffect()
            self._titilacion_effect.setColor(QColor(255, 100, 100))
            self._titilacion_effect.setStrength(0.0)
            cast("QGraphicsPixmapItem", self).setGraphicsEffect(self._titilacion_effect)

            self._titilacion_timer = QTimer()
            self._titilacion_timer.timeout.connect(self._alternar_titilacion)
            self._titilacion_timer.start(500)

            self._titilacion_intensidad = 0.0
            self._titilacion_direccion = 1

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error iniciando titilación en %s: %s", self._nombre, e)

    def _alternar_titilacion(self) -> None:
        """Alterna la intensidad de la titilación."""
        try:
            if self._titilacion_effect:
                step = TITILATION_MAX_INTENSITY / 2
                self._titilacion_intensidad += step * self._titilacion_direccion

                if self._titilacion_intensidad >= TITILATION_MAX_INTENSITY:
                    self._titilacion_intensidad = TITILATION_MAX_INTENSITY
                    self._titilacion_direccion = -1
                elif self._titilacion_intensidad <= 0.0:
                    self._titilacion_intensidad = 0.0
                    self._titilacion_direccion = 1

                self._titilacion_effect.setStrength(self._titilacion_intensidad)

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error en titilación de %s: %s", self._nombre, e)

    def detener_titilacion_batalla(self) -> None:
        """Detiene el efecto de titilación."""
        try:
            if self._titilacion_timer:
                self._titilacion_timer.stop()
                self._titilacion_timer = None

            if self._titilacion_effect:
                cast("QGraphicsPixmapItem", self).setGraphicsEffect(
                    None  # type: ignore[arg-type]
                )
                self._titilacion_effect = None

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error deteniendo titilación en %s: %s", self._nombre, e)

    def mostrar_perdida_flotante(self, perdidas: int) -> None:
        """Muestra una animación de pérdidas flotantes en rojo."""
        try:
            if self._perdida_flotante:
                if self._perdida_flotante.scene():
                    self._perdida_flotante.scene().removeItem(self._perdida_flotante)
                self._perdida_flotante = None

            texto = f"-{perdidas}"
            self._perdida_flotante = QGraphicsTextItem(texto)
            self._perdida_flotante.setParentItem(cast("QGraphicsPixmapItem", self))

            font = QFont("Arial", 16, QFont.Weight.Bold)
            self._perdida_flotante.setFont(font)
            self._perdida_flotante.setDefaultTextColor(QColor(255, 0, 0))

            pos_x = self._army_x - 10
            pos_y = self._army_y - 30
            self._perdida_flotante.setPos(pos_x, pos_y)

            self._animar_perdida_flotante()

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error mostrando pérdida flotante en %s: %s", self._nombre, e)

    def _animar_perdida_flotante(self) -> None:
        """Anima la pérdida flotante (movimiento hacia arriba y desvanecimiento)."""
        try:
            if not self._perdida_flotante:
                return

            opacity_effect = QGraphicsOpacityEffect()
            self._perdida_flotante.setGraphicsEffect(opacity_effect)

            self._opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
            self._opacity_animation.setDuration(2000)
            self._opacity_animation.setStartValue(1.0)
            self._opacity_animation.setEndValue(0.0)
            self._opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

            self._opacity_animation.finished.connect(self._limpiar_perdida_flotante)

            self._opacity_animation.start()

            self._movimiento_timer = QTimer()
            self._movimiento_timer.timeout.connect(self._mover_perdida_arriba)
            self._movimiento_timer.start(50)

            QTimer.singleShot(2000, self._detener_movimiento)

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error animando pérdida flotante en %s: %s", self._nombre, e)

    def _mover_perdida_arriba(self) -> None:
        """Mueve la pérdida flotante hacia arriba gradualmente."""
        try:
            if self._perdida_flotante:
                pos_actual = self._perdida_flotante.pos()
                nueva_pos = pos_actual + cast("QGraphicsPixmapItem", self).mapFromScene(
                    0, -1
                )
                self._perdida_flotante.setPos(nueva_pos.x(), nueva_pos.y())

        except (AttributeError, RuntimeError) as e:
            _LOG.debug("Error moviendo pérdida flotante: %s", e)

    def _detener_movimiento(self) -> None:
        """Detiene el timer de movimiento."""
        try:
            if hasattr(self, "_movimiento_timer") and self._movimiento_timer:
                self._movimiento_timer.stop()
                self._movimiento_timer = None
        except (AttributeError, RuntimeError) as e:
            _LOG.debug("Error deteniendo movimiento: %s", e)

    def _limpiar_perdida_flotante(self) -> None:
        """Limpia la pérdida flotante después de la animación."""
        try:
            if self._perdida_flotante:
                if self._perdida_flotante.scene():
                    self._perdida_flotante.scene().removeItem(self._perdida_flotante)
                self._perdida_flotante = None

        except (AttributeError, RuntimeError) as e:
            _LOG.debug("Error limpiando pérdida flotante: %s", e)
