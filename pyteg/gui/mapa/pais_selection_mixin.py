"""Selección visual y entrada por clic para el país en el mapa."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGraphicsPixmapItem,
    QGraphicsSceneMouseEvent,
)

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class PaisSelectionMixin:
    """Oscurecimiento por selección y clic para delegar en `selection_manager`."""

    _nombre: str
    _main_window: MainWindowProtocol | None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja los clics del mouse en el país."""
        if event.button() == Qt.MouseButton.LeftButton:
            if (
                self._main_window is not None
                and self._main_window.scene is not None
                and hasattr(self._main_window.scene, "selection_manager")
            ):
                self._main_window.scene.selection_manager.seleccionar_pais(self._nombre)
        else:
            item = cast("QGraphicsPixmapItem", self)
            QGraphicsPixmapItem.mousePressEvent(item, event)

    def set_seleccion_visual(self, tipo: str) -> None:
        """Establece el indicador visual de selección usando oscurecimiento."""
        self.limpiar_seleccion_visual()
        item = cast("QGraphicsPixmapItem", self)

        if tipo == "origen":
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.7)
            item.setGraphicsEffect(effect)
        elif tipo == "destino":
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.5)
            item.setGraphicsEffect(effect)

    def limpiar_seleccion_visual(self) -> None:
        """Elimina el indicador visual de selección."""
        item = cast("QGraphicsPixmapItem", self)
        if item.graphicsEffect():
            item.setGraphicsEffect(None)  # type: ignore[arg-type]
