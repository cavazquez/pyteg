from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar


class ToolBar(QToolBar):

    def __init__(self, texto):
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
