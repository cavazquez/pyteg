"""Módulo para la vista gráfica personalizada del mapa."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class QCustomGraphicsView(QGraphicsView):
    """Vista gráfica personalizada para mostrar el mapa del juego."""

    def __init__(
        self,
        scene: QGraphicsScene,
        main_window: Any,
        parent: QGraphicsView | None = None,
    ) -> None:
        """Inicializa la vista gráfica personalizada.

        Args:
            scene: Escena gráfica a mostrar.
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional).

        """
        super().__init__(scene, parent)
        self.main_window = main_window
        self.setMouseTracking(True)

        # Configurar el escalado automático
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ajustar la vista inicial al contenido
        self.fitInView(
            scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Maneja el movimiento del mouse en la vista.

        Args:
            event: Evento de movimiento del mouse.

        """
        super().mouseMoveEvent(event)
        # Aquí no hacemos nada porque el evento será manejado por la escena

    def reset_zoom(self) -> None:
        """Resetear el zoom para ajustar toda la escena en la vista."""
        if self.scene():
            self.fitInView(
                self.scene().sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """Manejar el redimensionamiento de la vista para escalar el mapa."""
        super().resizeEvent(event)
        if self.scene():
            # Ajustar la vista al contenido manteniendo la proporción
            self.fitInView(
                self.scene().sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        """Permitir zoom con la rueda del mouse."""
        # Factor de zoom
        zoom_factor = 1.15

        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def leaveEvent(self, event: QMouseEvent | QEvent) -> None:  # noqa: N802
        """Maneja el evento cuando el mouse sale de la vista.

        Args:
            event: Evento de salida del mouse.

        """
        # Limpiar la barra de estado cuando el mouse salga de la vista
        self.main_window.clear_status_bar()
        super().leaveEvent(event)
