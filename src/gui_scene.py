from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QGraphicsScene,
)


class QCustomGraphicsScene(QGraphicsScene):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        # Obtener las coordenadas del mouse en la escena
        scene_pos = event.scenePos()
        self.main_window.update_status_bar(
            f"Coordenadas: ({scene_pos.x()}, {scene_pos.y()})",
        )
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QMouseEvent):  # noqa: N802
        self.main_window.clear_status_bar()
        super().leaveEvent(event)
