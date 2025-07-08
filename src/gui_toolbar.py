from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSizePolicy, QToolBar, QToolButton, QWidget


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

        # Botón para finalizar el turno
        button_finalizar_turno = QAction(
            QIcon("icons/finish.png"), "Finalizar Turno", self
        )
        button_finalizar_turno.triggered.connect(main_window.finalizar_turno)
        self.addAction(button_finalizar_turno)

        # Botón de ajustes
        self.size_menu = QMenu(self)

        # Acciones para los tamaños predefinidos
        size_actions = [
            ("Pequeño (800x600)", 800, 600),
            ("Mediano (1024x768)", 1024, 768),
            ("Grande (1280x800)", 1280, 800),
            ("Pantalla Completa", 0, 0),  # 0,0 indicará pantalla completa
        ]

        for text, width, height in size_actions:
            action = QAction(text, self)
            if width == 0 and height == 0:  # Caso especial para pantalla completa
                action.triggered.connect(lambda: self.resize_window(0, 0))
            else:
                action.triggered.connect(partial(self.resize_window, width, height))
            self.size_menu.addAction(action)

        # Crear botón de menú
        size_button = QToolButton(self)
        size_button.setText("Tamaño")
        size_button.setPopupMode(QToolButton.InstantPopup)
        size_button.setMenu(self.size_menu)

        # Agregar el botón a la barra de herramientas
        self.addWidget(size_button)

        # Expansor derecho
        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(right_spacer)

        # Guardar referencia a la ventana principal
        self.main_window = main_window

    def resize_window(self, width, height):
        """Cambia el tamaño de la ventana principal"""
        if width == 0 or height == 0:  # Pantalla completa
            self.main_window.showFullScreen()
        else:
            # Asegurarse de salir del modo pantalla completa
            self.main_window.showNormal()
            self.main_window.resize(width, height)
