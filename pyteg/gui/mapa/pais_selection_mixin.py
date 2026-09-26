"""Selección visual y entrada por clic para el país en el mapa."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsPixmapItem,
    QGraphicsSceneMouseEvent,
)

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class PaisSelectionMixin:
    """Oscurecimiento por selección y clic para delegar en `selection_manager`."""

    _nombre: str
    _main_window: MainWindowProtocol | None
    _seleccion_visual: str | None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Delega la selección a la escena (soporta superposiciones)."""
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self._main_window
            if (
                main_window is not None
                and main_window.scene is not None
                and hasattr(main_window.scene, "handle_country_click")
            ) and main_window.scene.handle_country_click(
                event.scenePos(), event.screenPos()
            ):
                event.accept()
                return
        item = cast("QGraphicsPixmapItem", self)
        QGraphicsPixmapItem.mousePressEvent(item, event)

    def set_seleccion_visual(self, tipo: str) -> None:
        """Oscurece el país según su rol, sin transparentarlo ni afectar sus marcas."""
        if tipo not in {"origen", "destino"}:
            self.limpiar_seleccion_visual()
            return
        self._seleccion_visual = tipo
        self._restaurar_efecto_seleccion()

    def limpiar_seleccion_visual(self) -> None:
        """Elimina el indicador visual de selección."""
        self._seleccion_visual = None
        item = cast("QGraphicsPixmapItem", self)
        if getattr(self, "_titilacion_effect", None) is None:
            item.setGraphicsEffect(None)  # type: ignore[arg-type]
        item.update()

    def _restaurar_efecto_seleccion(self) -> None:
        """Aplica el sombreado si no hay una animación de batalla activa."""
        if (
            self._seleccion_visual is None
            or getattr(self, "_titilacion_effect", None) is not None
        ):
            return

        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(0, 0, 0))
        effect.setStrength(0.55 if self._seleccion_visual == "origen" else 0.75)
        cast("QGraphicsPixmapItem", self).setGraphicsEffect(effect)
