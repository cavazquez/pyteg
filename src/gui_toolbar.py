from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class ToolBar(QToolBar):
    def __init__(self, texto, main_window):
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)

        button_conectar = QAction("Conectar", self)
        button_conectar.triggered.connect(main_window.abrir_ventana_conectar)
        self.addAction(button_conectar)
