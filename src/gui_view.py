from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QGraphicsView,
)


class QCustomGraphicsView(QGraphicsView):
    def __init__(self, scene, main_window, parent=None):
        super().__init__(scene, parent)
        self.main_window = main_window
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        super().mouseMoveEvent(event)
        # Aquí no hacemos nada porque el evento será manejado por la escena

    def leaveEvent(self, event):  # noqa: N802
        # Limpiar la barra de estado cuando el mouse salga de la vista
        self.main_window.clear_status_bar()
        super().leaveEvent(event)
