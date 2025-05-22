from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QSizePolicy, QToolBar, QWidget


class ToolBar(QToolBar):
    def __init__(self, texto, main_window):
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)

        # Expansor izquierdo
        left_spacer = QWidget(self)
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(left_spacer)

        button_conectar = QAction(QIcon("icons/conectar.png"), "Conectar", self)
        button_conectar.triggered.connect(main_window.abrir_ventana_conectar)
        self.addAction(button_conectar)

        button_atacar = QAction(QIcon("icons/atacar.png"), "Atacar", self)
        # button_atacar.triggered.connect(main_window.abrir_ventana_atacar)
        self.addAction(button_atacar)

        button_mover = QAction(QIcon("icons/mover.png"), "Mover", self)
        # button_mover.triggered.connect(main_window.abrir_ventana_mover)
        self.addAction(button_mover)

        # Expansor derecho
        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(right_spacer)
