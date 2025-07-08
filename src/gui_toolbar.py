import contextlib
from functools import partial

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)


class ToolBar(QToolBar):
    def __init__(self, texto, main_window):
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.main_window = main_window

        # Configurar la barra de herramientas
        self._setup_spacers()
        self._setup_action_buttons()
        self._setup_size_menu()

    def _setup_spacers(self):
        """Configura los espaciadores en la barra de herramientas"""
        # Expansor izquierdo
        left_spacer = QWidget(self)
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(left_spacer)

        # El expansor derecho se añade después de todos los botones

    def _setup_action_buttons(self):
        """Configura los botones de acción en la barra de herramientas"""
        # Botón conectar
        button_conectar = QAction(QIcon("icons/conectar.png"), "Conectar", self)
        button_conectar.triggered.connect(self.main_window.abrir_ventana_conectar)
        self.addAction(button_conectar)

        # Botón atacar
        button_atacar = QAction(QIcon("icons/atacar.png"), "Atacar", self)
        # button_atacar.triggered.connect(self.main_window.abrir_ventana_atacar)
        self.addAction(button_atacar)

        # Botón mover
        button_mover = QAction(QIcon("icons/mover.png"), "Mover", self)
        # button_mover.triggered.connect(self.main_window.abrir_ventana_mover)
        self.addAction(button_mover)

        # Botón para finalizar el turno
        button_finalizar_turno = QAction(
            QIcon("icons/finish.png"), "Finalizar Turno", self
        )
        button_finalizar_turno.triggered.connect(self.main_window.finalizar_turno)
        self.addAction(button_finalizar_turno)

    def _setup_size_menu(self):
        """Configura el menú de tamaño y su botón"""
        # Crear y configurar el menú
        self.size_menu = self._create_size_menu()

        # Crear botón de menú con ícono
        size_button = self._create_size_button()

        # Agregar el botón a la barra de herramientas
        self.addWidget(size_button)

        # Expansor derecho (se añade aquí después de todos los botones)
        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(right_spacer)

    def _create_size_menu(self):
        """Crea el menú de tamaño con todas sus opciones"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 30px;
                border-radius: 3px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4361ee;
                color: white;
            }
            QMenu::icon {
                padding-left: 10px;
            }
            QMenu::separator {
                height: 1px;
                background: #dee2e6;
                margin: 5px 10px;
            }
        """)

        # Sección de tamaños predefinidos
        menu.addSection("Tamaños predefinidos")

        # Acciones para los tamaños predefinidos con íconos
        size_actions = [
            ("Pequeño (800x600)", 800, 600, "icons/size_small.png"),
            ("Mediano (1024x768)", 1024, 768, "icons/size_medium.png"),
            ("Grande (1280x800)", 1280, 800, "icons/size_large.png"),
        ]

        for text, width, height, icon_path in size_actions:
            action = QAction(text, self)
            with contextlib.suppress(Exception):
                action.setIcon(QIcon(icon_path))
            action.triggered.connect(partial(self.resize_window, width, height))
            menu.addAction(action)

        # Separador
        menu.addSeparator()

        # Opciones de pantalla completa
        fullscreen_action = QAction("Pantalla Completa", self)
        with contextlib.suppress(Exception):
            fullscreen_action.setIcon(QIcon("icons/fullscreen.png"))
        fullscreen_action.triggered.connect(lambda: self.resize_window(0, 0))
        menu.addAction(fullscreen_action)

        # Opción para ajustar al tamaño de la pantalla
        fit_screen_action = QAction("Ajustar a la pantalla", self)
        with contextlib.suppress(Exception):
            fit_screen_action.setIcon(QIcon("icons/fit_screen.png"))
        fit_screen_action.triggered.connect(self.fit_to_screen)
        menu.addAction(fit_screen_action)

        # Separador
        menu.addSeparator()

        # Opción para restaurar tamaño por defecto
        default_action = QAction("Tamaño por defecto", self)
        with contextlib.suppress(Exception):
            default_action.setIcon(QIcon("icons/default_size.png"))
        default_action.triggered.connect(lambda: self.resize_window(1024, 768))
        menu.addAction(default_action)

        return menu

    def _create_size_button(self):
        """Crea el botón de tamaño con su estilo"""
        size_button = QToolButton(self)
        size_button.setIcon(QIcon("icons/resize.png"))
        size_button.setToolTip("Cambiar tamaño de la ventana")
        size_button.setPopupMode(QToolButton.InstantPopup)
        size_button.setMenu(self.size_menu)
        size_button.setIconSize(QSize(24, 24))

        # Estilo para el botón
        size_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: rgba(67, 97, 238, 0.1);
            }
            QToolButton:pressed {
                background-color: rgba(67, 97, 238, 0.2);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)

        return size_button

    def resize_window(self, width, height):
        """Cambia el tamaño de la ventana principal"""
        if width == 0 or height == 0:  # Pantalla completa
            self.main_window.showFullScreen()
        else:
            # Asegurarse de salir del modo pantalla completa
            self.main_window.showNormal()
            self.main_window.resize(width, height)
            # Centrar la ventana en la pantalla
            self.center_window()

    def fit_to_screen(self):
        """Ajusta la ventana al tamaño de la pantalla con un margen"""
        # Obtener el tamaño disponible de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        # Calcular un tamaño que sea el 90% del tamaño disponible
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        # Redimensionar y centrar
        self.main_window.showNormal()
        self.main_window.resize(width, height)
        self.center_window()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        frame_geometry = self.main_window.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.main_window.move(frame_geometry.topLeft())
