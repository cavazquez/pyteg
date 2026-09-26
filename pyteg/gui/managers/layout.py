"""Gestor de layout para la interfaz gráfica principal de PyTeg.

Maneja la creación y configuración de todos los elementos de layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui.managers.units_panel import setup_continent_values as _build_units_panel
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.gui.toolbar import ToolBar
from pyteg.gui.widgets.chat import Chat
from pyteg.gui.widgets.view import QCustomGraphicsView
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


_INITIAL_VIEW_SIZE = 1000
_INITIAL_CHAT_SIZE = 120
_SPLITTER_PARTS = 2


class LayoutManager:
    """Gestor de layout para la ventana principal."""

    def __init__(self, main_window: MainWindowProtocol) -> None:
        """Inicializar el gestor de layout.

        Args:
            main_window: Instancia de la ventana principal (Gui)

        """
        self.main_window = main_window
        self._chat_size_initialized = False
        self._sidebar_size_initialized = False

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
        # El ``sizeHint`` de QTextEdit es alto aunque el chat esté vacío.
        # Ignorar ese hint permite que el splitter use una reserva compacta.
        self.main_window.chat.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Ignored,
        )
        self.main_window.chat.setMinimumHeight(0)
        self.main_window.chat.show()

        # Agrego la barra de herramientas
        self.main_window.toolbar = ToolBar("My main toolbar", self.main_window)
        self.main_window.addToolBar(self.main_window.toolbar)

    def _setup_scene_and_view(self) -> None:
        """Configurar escena y vista gráfica."""
        # Agrego la escena y la vista
        self.main_window.scene = QCustomGraphicsScene(
            self.main_window,
            theme=self.main_window.map_theme,
        )
        self.main_window.view = QCustomGraphicsView(
            self.main_window.scene, self.main_window
        )

    def _create_vertical_splitter(self) -> QSplitter:
        """Crear splitter vertical para vista y chat.

        Returns:
            Splitter vertical creado.

        """
        vertical_splitter = QSplitter()
        vertical_splitter.setOrientation(Qt.Orientation.Vertical)
        vertical_splitter.setChildrenCollapsible(True)
        if self.main_window.view is not None:
            vertical_splitter.addWidget(self.main_window.view)
        if self.main_window.chat is not None:
            vertical_splitter.addWidget(self.main_window.chat)
        vertical_splitter.setCollapsible(0, False)  # noqa: FBT003
        vertical_splitter.setCollapsible(1, True)  # noqa: FBT003
        vertical_splitter.setStretchFactor(0, 1)
        vertical_splitter.setStretchFactor(1, 0)
        vertical_splitter.setSizes([_INITIAL_VIEW_SIZE, _INITIAL_CHAT_SIZE])
        vertical_splitter.setHandleWidth(6)
        self.main_window.vertical_splitter = vertical_splitter
        return vertical_splitter

    def _create_horizontal_splitter(self, vertical_splitter: QSplitter) -> QSplitter:
        """Crear splitter horizontal principal.

        Returns:
            Splitter horizontal creado.

        """
        # Create a horizontal splitter to hold the vertical splitter
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Orientation.Horizontal)
        horizontal_splitter.setChildrenCollapsible(True)
        horizontal_splitter.setHandleWidth(6)
        horizontal_splitter.addWidget(vertical_splitter)
        self.main_window.horizontal_splitter = horizontal_splitter
        return horizontal_splitter

    def _setup_right_column(self) -> None:
        """Configurar la columna derecha con unidades y jugadores."""
        # Widget principal para la columna derecha
        self.main_window.right_column_widget = QWidget()
        self.main_window.right_column_widget.setMinimumWidth(200)
        layout = QVBoxLayout(self.main_window.right_column_widget)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)

        # Añadir título y lista de jugadores
        self._add_players_title(layout)
        self._setup_players_list(layout)

        # Add a spacer to separate the player list from the values
        layout.addStretch()

        # Añadir las filas de unidades correspondientes al mapa activo.
        self._setup_continent_values(layout)

        # El contenido puede crecer con muchos jugadores; el scroll evita que
        # las últimas filas queden inaccesibles en ventanas bajas.
        right_column_scroll = QScrollArea()
        right_column_scroll.setWidgetResizable(True)
        right_column_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_column_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        right_column_scroll.setMinimumWidth(220)
        right_column_scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        right_column_scroll.setWidget(self.main_window.right_column_widget)
        self.main_window.right_column_scroll = right_column_scroll

    def _setup_continent_values(self, layout: QVBoxLayout) -> None:
        """Delega la construcción del panel UNIDADES en `units_panel`."""
        _build_units_panel(self.main_window, layout)

    def rebuild_units_panel(self) -> None:
        """Reconstruye las filas al cambiar el tema antes de conectarse.

        Raises:
            RuntimeError: Si todavía no existe la columna derecha.

        """
        layout = self.main_window.right_column_widget.layout()
        if layout is None:
            msg = "La columna de unidades aún no está construida"
            raise RuntimeError(msg)
        section = self.main_window.row_widgets.get("Generales")
        if section is not None:
            old_section = section.parentWidget()
            if old_section is not None:
                layout.removeWidget(old_section)
                old_section.setParent(None)
                old_section.deleteLater()
        _build_units_panel(self.main_window, cast("QVBoxLayout", layout))

    def _add_players_title(self, layout: QVBoxLayout) -> None:
        """Agregar título de la sección de jugadores."""
        # Título para la sección de jugadores
        players_title = QLabel(_("JUGADORES"))
        self.main_window.players_title_label = players_title
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
        horizontal_splitter.addWidget(self.main_window.right_column_scroll)
        horizontal_splitter.setCollapsible(0, False)  # noqa: FBT003
        horizontal_splitter.setCollapsible(1, True)  # noqa: FBT003
        horizontal_splitter.setStretchFactor(0, 1)
        horizontal_splitter.setStretchFactor(1, 0)

        # Create a widget to hold the QGraphicsView and input area
        self.main_window.main_widget = QWidget(cast("QWidget", self.main_window))
        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(horizontal_splitter, 0, 0)
        self.main_window.main_widget.setLayout(main_layout)
        self.main_window.setCentralWidget(self.main_window.main_widget)

    def update_responsive_layout(self, width: int, height: int) -> None:
        """Da tamaños compactos iniciales y luego respeta el ajuste del usuario.

        Qt conserva los tamaños de los splitters al redimensionar la ventana.
        Reaplicar proporciones en cada ``resizeEvent`` desharía los cambios que
        el usuario haya hecho con sus divisores.
        """
        vertical = getattr(self.main_window, "vertical_splitter", None)
        if (
            not self._chat_size_initialized
            and vertical is not None
            and vertical.isVisible()
            and height > 0
        ):
            sizes = vertical.sizes()
            chat_colapsado = (
                len(sizes) == _SPLITTER_PARTS and sizes[0] > 0 and sizes[1] == 0
            )
            if len(sizes) == _SPLITTER_PARTS:
                if vertical.widget(1).isVisible() and not chat_colapsado:
                    chat_size = min(160, max(72, round(height * 0.18)))
                    vertical.setSizes([max(1, height - chat_size), chat_size])
                self._chat_size_initialized = True

        horizontal = getattr(self.main_window, "horizontal_splitter", None)
        sidebar = getattr(self.main_window, "right_column_scroll", None)
        if (
            self._sidebar_size_initialized
            or horizontal is None
            or sidebar is None
            or not sidebar.isVisible()
            or width <= 0
        ):
            return
        sizes = horizontal.sizes()
        if len(sizes) != _SPLITTER_PARTS:
            return
        if not (sizes[0] > 0 and sizes[1] == 0):
            sidebar_size = min(300, max(220, round(width * 0.22)))
            horizontal.setSizes([max(1, width - sidebar_size), sidebar_size])
        self._sidebar_size_initialized = True
