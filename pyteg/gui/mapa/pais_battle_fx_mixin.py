"""Efectos visuales de batalla y misiles sobre un país del mapa."""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
)

from pyteg.config import TITILATION_MAX_INTENSITY
from pyteg.gui.animation_timing import UNIT_GAIN_DURATION_MS, UNIT_LOSS_DURATION_MS
from pyteg.gui.mapa.army_position import resolve_army_position
from pyteg.gui.widgets.circulo import Circulo
from pyteg.gui.widgets.missile_badge import MissileBadge
from pyteg.gui.widgets.unit_delta import UnitDeltaIndicator
from pyteg.logger import get_logger

_LOG = get_logger("gui.pais.fx")


class PaisBattleFxMixin:
    """Titilación, pérdidas flotantes e indicador de misiles (país)."""

    _nombre: str
    _army_x: float
    _army_y: float
    _misiles_badge: MissileBadge | None
    _misiles_text: QGraphicsTextItem | None
    _cantidad_misiles: int
    _titilacion_timer: QTimer | None
    _titilacion_effect: QGraphicsColorizeEffect | None
    _titilacion_outline: QGraphicsPathItem | None
    _titilacion_intensidad: float
    _titilacion_direccion: int
    _perdida_flotante: UnitDeltaIndicator | None
    _refuerzo_flotante: UnitDeltaIndicator | None
    _opacity_animation: QPropertyAnimation | None
    _movimiento_timer: QTimer | None

    def actualizar_misiles(self, cantidad: int) -> None:
        """Actualiza el indicador visual de misiles en el país."""
        try:
            self._cantidad_misiles = cantidad

            if cantidad <= 0:
                if self._misiles_badge:
                    self._misiles_badge.setVisible(False)
                if self._misiles_text:
                    self._misiles_text.setVisible(False)
                actualizar_tooltip = getattr(self, "_actualizar_tooltip", None)
                if callable(actualizar_tooltip):
                    actualizar_tooltip()
                return

            if self._misiles_badge is None or self._misiles_text is None:
                self._misiles_badge = MissileBadge()
                self._misiles_text = self._misiles_badge.count_text

            badge = self._misiles_badge
            text = self._misiles_text
            if badge is None or text is None:
                return

            badge.set_count(cantidad)
            text.setVisible(True)
            badge.setVisible(True)

            self._position_missile_badge(badge)

            actualizar_tooltip = getattr(self, "_actualizar_tooltip", None)
            if callable(actualizar_tooltip):
                actualizar_tooltip()
            badge.setToolTip(cast("QGraphicsPixmapItem", self).toolTip())

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error actualizando misiles en %s: %s", self._nombre, e)

    def _position_missile_badge(self, badge: MissileBadge) -> None:
        circle = getattr(self, "_circle", None)
        if circle is not None:
            # La escena eleva la ficha por encima de los países vecinos.
            # El misil comparte su posición y su capa, incluso después
            # de separar la ficha del sprite del país.
            scene = circle.scene()
            obstacles = list(getattr(scene, "country_label_bounds", ()))
            if scene is not None:
                obstacles.extend(
                    item.sceneBoundingRect().adjusted(-1, -1, 1, 1)
                    for item in scene.items()
                    if isinstance(item, (Circulo, MissileBadge))
                    and item is not circle
                    and item is not badge
                    and item.isVisible()
                )
            badge.place_next_to(circle, obstacles)
            return

        country = cast("QGraphicsPixmapItem", self)
        badge.setParentItem(country)
        pixmap = country.pixmap()
        x, y = resolve_army_position(
            pixmap.width(), pixmap.height(), self._army_x, self._army_y
        )
        marker = QRectF(x, y, 16, 16)
        badge.setPos(
            marker.center().x() - badge.rect().width() / 2,
            marker.bottom() + 2,
        )

    def iniciar_titilacion_batalla(self) -> None:
        """Inicia el efecto de titilación durante una batalla."""
        try:
            self.detener_titilacion_batalla()

            self._titilacion_effect = QGraphicsColorizeEffect()
            self._titilacion_effect.setColor(QColor(255, 100, 100))
            self._titilacion_effect.setStrength(TITILATION_MAX_INTENSITY)
            country = cast("QGraphicsPixmapItem", self)
            country.setGraphicsEffect(self._titilacion_effect)

            scene = country.scene()
            if scene is not None:
                outline = QGraphicsPathItem(country.mapToScene(country.shape()))
                pen = QPen(QColor("#D32F2F"), 3)
                pen.setCosmetic(True)
                outline.setPen(pen)
                outline.setZValue(900)
                outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                scene.addItem(outline)
                self._titilacion_outline = outline

            self._titilacion_timer = QTimer(self._titilacion_effect)
            self._titilacion_timer.timeout.connect(self._alternar_titilacion)
            self._titilacion_timer.start(500)

            self._titilacion_intensidad = TITILATION_MAX_INTENSITY
            self._titilacion_direccion = -1

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
                if self._titilacion_outline is not None:
                    self._titilacion_outline.setOpacity(
                        max(0.3, self._titilacion_intensidad / TITILATION_MAX_INTENSITY)
                    )

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error en titilación de %s: %s", self._nombre, e)

    def detener_titilacion_batalla(self) -> None:
        """Detiene el efecto de titilación."""
        try:
            outline = getattr(self, "_titilacion_outline", None)
            if outline is not None:
                scene = outline.scene()
                if scene is not None:
                    scene.removeItem(outline)
                self._titilacion_outline = None
            if self._titilacion_timer:
                self._titilacion_timer.stop()
                self._titilacion_timer.deleteLater()
                self._titilacion_timer = None

            if self._titilacion_effect:
                cast("QGraphicsPixmapItem", self).setGraphicsEffect(
                    None  # type: ignore[arg-type]
                )
                self._titilacion_effect = None
                if getattr(self, "_seleccion_visual", None) is not None:
                    restaurar = getattr(self, "_restaurar_efecto_seleccion", None)
                    if callable(restaurar):
                        restaurar()

        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error deteniendo titilación en %s: %s", self._nombre, e)

    def mostrar_perdida_flotante(self, perdidas: int) -> None:
        """Muestra una animación de pérdidas flotantes en rojo."""
        if perdidas > 0:
            self._mostrar_cambio_flotante(
                -perdidas, "_perdida_flotante", UNIT_LOSS_DURATION_MS
            )

    def mostrar_refuerzo_flotante(self, cantidad: int) -> None:
        """Señala con +N las unidades recibidas, en verde y junto a su ficha."""
        if cantidad > 0:
            self._mostrar_cambio_flotante(
                cantidad, "_refuerzo_flotante", UNIT_GAIN_DURATION_MS
            )

    def _mostrar_cambio_flotante(
        self, cantidad: int, attribute: str, duration_ms: int
    ) -> None:
        try:
            circle = getattr(self, "_circle", None)
            if circle is None:
                return
            previous = getattr(self, attribute, None)
            if previous is not None:
                previous.stop()
                previous.deleteLater()
            indicator = UnitDeltaIndicator(cantidad, circle, duration_ms)
            setattr(self, attribute, indicator)

            def finished() -> None:
                if getattr(self, attribute, None) is indicator:
                    setattr(self, attribute, None)

            indicator.fade_animation.finished.connect(finished)
            if cantidad < 0:
                self._movimiento_timer = indicator.movement_timer
                self._opacity_animation = indicator.fade_animation
            indicator.start()
        except (AttributeError, RuntimeError) as e:
            _LOG.warning(
                "Error mostrando cambio de unidades en %s: %s", self._nombre, e
            )
