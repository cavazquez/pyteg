"""Gestor de layout para la interfaz gráfica principal de PyTeg.

Maneja la creación y configuración de todos los elementos de layout.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui.managers.units_panel import setup_continent_values as _build_units_panel
from pyteg.gui_chat import Chat
from pyteg.gui_scene import QCustomGraphicsScene
from pyteg.gui_toolbar import ToolBar
from pyteg.gui_view import QCustomGraphicsView


class LayoutManager:
    """Gestor de layout para la ventana principal."""

    def __init__(self, main_window: Any) -> None:
        """Inicializar el gestor de layout.

        Args:
            main_window: Instancia de la ventana principal (Gui)

        """
        self.main_window = main_window

    def setup_graphics_view(self) -> None:
        """Configurar la vista gráfica principal."""
        self._setup_chat_and_toolbar()
        self._setup_scene_and_view()

        # Crear splitters
        vertical_splitter = self._create_vertical_splitter()
        horizontal_splitter = self._create_horizontal_splitter(vertical_splitter)

        # Configurar columna derecha
        self._setup_right_column()

        # Configurar layout principal
        self._setup_main_layout(horizontal_splitter)

    def _setup_chat_and_toolbar(self) -> None:
        """Configurar chat y toolbar."""
        # Agrego el Chat
        self.main_window.chat = Chat(self.main_window)
        self.main_window.chat.show()

        # Agrego la barra de herramientas
        self.main_window.toolbar = ToolBar("My main toolbar", self.main_window)
        self.main_window.addToolBar(self.main_window.toolbar)

    def _setup_scene_and_view(self) -> None:
        """Configurar escena y vista gráfica."""
        # Agrego la escena y la vista
        self.main_window.scene = QCustomGraphicsScene(self.main_window)
        self.main_window.view = QCustomGraphicsView(
            self.main_window.scene, self.main_window
        )

    def _create_vertical_splitter(self) -> QSplitter:
        """Crear splitter vertical para vista y chat.

        Returns:
            Splitter vertical creado.

        """
        # Create a splitter to hold the QGraphicsView and Chat
        vertical_splitter = QSplitter()
        vertical_splitter.setOrientation(Qt.Orientation.Vertical)
        vertical_splitter.addWidget(self.main_window.view)
        vertical_splitter.addWidget(self.main_window.chat)
        vertical_splitter.setStretchFactor(0, 9)  # 90% for QGraphicsView
        vertical_splitter.setStretchFactor(1, 1)  # 10% for Chat
        return vertical_splitter

    def _create_horizontal_splitter(self, vertical_splitter: QSplitter) -> QSplitter:
        """Crear splitter horizontal principal.

        Returns:
            Splitter horizontal creado.

        """
        # Create a horizontal splitter to hold the vertical splitter
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(vertical_splitter)
        return horizontal_splitter

    def _setup_right_column(self) -> None:
        """Configurar la columna derecha con unidades y jugadores."""
        # Widget principal para la columna derecha
        self.main_window.right_column_widget = QWidget()
        layout = QVBoxLayout(self.main_window.right_column_widget)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)

        # Añadir título y lista de jugadores
        self._add_players_title(layout)
        self._setup_players_list(layout)

        # Add a spacer to separate the player list from the values
        layout.addStretch()

        # Add the 6 values below the player list
        self._setup_continent_values(layout)

    def _setup_continent_values(self, layout: QVBoxLayout) -> None:
        """Delega la construcción del panel UNIDADES en `units_panel`."""
        _build_units_panel(self.main_window, layout)

    def _add_players_title(self, layout: QVBoxLayout) -> None:
        """Agregar título de la sección de jugadores."""
        # Título para la sección de jugadores
        players_title = QLabel("JUGADORES")
        players_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        players_title.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                border-bottom: 2px solid #4361ee;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(players_title)

    def _setup_players_list(self, layout: QVBoxLayout) -> None:
        """Configurar la lista de jugadores."""
        # Crear un contenedor para la lista de jugadores sin scroll
        players_container = QWidget()
        players_layout = QVBoxLayout(players_container)
        players_layout.setContentsMargins(0, 0, 0, 0)
        players_layout.setSpacing(6)

        # Add a list of players to the right column
        self.main_window.player_labels = []
        self._create_player_widgets(players_layout)

        # Añadir un espaciador al final de la lista de jugadores
        players_layout.addStretch()

        # Añadir el contenedor al layout principal
        layout.addWidget(players_container)

    def _create_player_widgets(self, layout: QVBoxLayout) -> None:
        """Crear widgets iniciales para jugadores."""
        # Inicializar lista vacía - se crearán dinámicamente
        self.main_window.players_layout = layout

    def _setup_main_layout(self, horizontal_splitter: QSplitter) -> None:
        """Configurar el layout principal de la ventana."""
        # Agregar columna derecha al splitter
        horizontal_splitter.addWidget(self.main_window.right_column_widget)

        # Create a widget to hold the QGraphicsView and input area
        self.main_window.main_widget = QWidget(self.main_window)
        main_layout = QGridLayout()
        main_layout.addWidget(horizontal_splitter, 0, 0)
        self.main_window.main_widget.setLayout(main_layout)
        self.main_window.setCentralWidget(self.main_window.main_widget)

        # Configurar factores de estiramiento para el splitter horizontal
        horizontal_splitter.setStretchFactor(0, 8)  # 80% for the left side
        horizontal_splitter.setStretchFactor(1, 2)  # 20% for the right column
