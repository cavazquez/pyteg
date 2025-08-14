"""
Gestor de layout para la interfaz gráfica principal de PyTeg.
Maneja la creación y configuración de todos los elementos de layout.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.gui_chat import Chat
from src.gui_scene import QCustomGraphicsScene
from src.gui_toolbar import ToolBar
from src.gui_view import QCustomGraphicsView


class LayoutManager:
    """Gestor de layout para la ventana principal."""

    def __init__(self, main_window):
        """Inicializar el gestor de layout.

        Args:
            main_window: Instancia de la ventana principal (Gui)
        """
        self.main_window = main_window

    def setup_graphics_view(self):
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

    def _setup_chat_and_toolbar(self):
        """Configurar chat y toolbar."""
        # Agrego el Chat
        self.main_window.chat = Chat(self.main_window)
        self.main_window.chat.show()

        # Agrego la barra de herramientas
        self.main_window.toolbar = ToolBar("My main toolbar", self.main_window)
        self.main_window.addToolBar(self.main_window.toolbar)

    def _setup_scene_and_view(self):
        """Configurar escena y vista gráfica."""
        # Agrego la escena y la vista
        self.main_window.scene = QCustomGraphicsScene(self.main_window)
        self.main_window.view = QCustomGraphicsView(
            self.main_window.scene, self.main_window
        )

    def _create_vertical_splitter(self):
        """Crear splitter vertical para vista y chat."""
        # Create a splitter to hold the QGraphicsView and Chat
        vertical_splitter = QSplitter()
        vertical_splitter.setOrientation(Qt.Vertical)
        vertical_splitter.addWidget(self.main_window.view)
        vertical_splitter.addWidget(self.main_window.chat)
        vertical_splitter.setStretchFactor(0, 9)  # 90% for QGraphicsView
        vertical_splitter.setStretchFactor(1, 1)  # 10% for Chat
        return vertical_splitter

    def _create_horizontal_splitter(self, vertical_splitter):
        """Crear splitter horizontal principal."""
        # Create a horizontal splitter to hold the vertical splitter
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Horizontal)
        horizontal_splitter.addWidget(vertical_splitter)
        return horizontal_splitter

    def _setup_right_column(self):
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

    def _setup_continent_values(self, layout):
        """Crea la sección UNIDADES con filas ordenadas e íconos."""
        # Contenedor principal de la sección
        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        section.setObjectName("unitsSection")
        # Se aplicará stylesheet en _apply_units_theme()

        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(6)

        title = QLabel("UNIDADES")
        title.setAlignment(Qt.AlignLeft)
        title.setObjectName("unitsTitle")
        section_layout.addWidget(title)

        # Diccionario de labels reutilizable en updates
        self.main_window.value_labels = {}
        self.main_window._row_widgets = {}  # noqa: SLF001
        self.main_window._last_units = {}  # noqa: SLF001

        # Fila: Generales
        self._create_unit_row(
            section_layout,
            key="Generales",
            value=0,
            icon_color="#2E7D32",
            glyph="G",
            tooltip="Unidades generales disponibles para colocar",
        )

        # Fila: Misiles (inicialmente 0 y oculta si no hay)
        self._create_unit_row(
            section_layout,
            key="Misiles",
            value=0,
            icon_color="#D32F2F",
            glyph="M",
            tooltip="Misiles disponibles",
        )
        # Se ocultará por defecto hasta que haya valor > 0
        self.main_window._row_widgets["Misiles"].setVisible(False)  # noqa: SLF001

        # Filas de continentes (incluye Oceanía)
        for cont in [
            "América del Sur",
            "América del Norte",
            "Europa",
            "Asia",
            "África",
            "Oceanía",
        ]:
            self._create_unit_row(
                section_layout,
                key=cont,
                value=0,
                icon_color="#1565C0",
                glyph="C",
                tooltip=f"Refuerzos por control de {cont}",
            )

        layout.addWidget(section)
        self.main_window._apply_units_theme(section)  # noqa: SLF001

    def _create_unit_row(  # noqa: PLR0913, PLR0917
        self,
        parent_layout,
        key: str,
        value: int,
        icon_color: str,
        glyph: str,
        tooltip: str,
    ):
        """Crea una fila (ícono dibujado + etiqueta) y la registra en value_labels."""
        row = QFrame()
        row.setObjectName("unitRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 4, 4, 4)
        row_layout.setSpacing(6)

        icon_label = self._make_circle_icon(icon_color, glyph)
        row_layout.addWidget(icon_label)

        label = QLabel(f"{key}: {value}")
        label.setObjectName("unitRowLabel")
        row_layout.addWidget(label)

        # Empujar contenido a la izquierda
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row_layout.addWidget(spacer)

        parent_layout.addWidget(row)
        self.main_window.value_labels[key] = label
        self.main_window._row_widgets[key] = row  # noqa: SLF001
        # Tooltip de toda la fila
        row.setToolTip(tooltip)

    def _make_circle_icon(self, color_hex: str, glyph: str | None) -> QLabel:
        """Crea un QLabel con un QPixmap de círculo y opcional glifo."""

        size = 16
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(QColor(color_hex))
        painter.drawEllipse(0, 0, size - 1, size - 1)
        if glyph:
            painter.setPen(QColor("white"))
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pm.rect(), Qt.AlignCenter, glyph)
        painter.end()
        label = QLabel()
        label.setPixmap(pm)
        return label

    def _add_players_title(self, layout):
        """Agregar título de la sección de jugadores."""
        # Título para la sección de jugadores
        players_title = QLabel("JUGADORES")
        players_title.setAlignment(Qt.AlignCenter)
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

    def _setup_players_list(self, layout):
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

    def _create_player_widgets(self, layout):
        """Crear widgets iniciales para jugadores."""
        # Inicializar lista vacía - se crearán dinámicamente
        self.main_window.players_layout = layout

    def _setup_main_layout(self, horizontal_splitter):
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
