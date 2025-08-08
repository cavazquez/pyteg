import contextlib

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.client_transmisor import ClientNullTransmisor
from src.cliente_colores import Colores
from src.debug_logger import debug_logger
from src.gui_admin import VentanaAdmin
from src.gui_attack_dialog import AttackDialog
from src.gui_chat import Chat
from src.gui_conectar import VentanaConectar
from src.gui_esperar_jugadores import VentanaEsperarJugadores
from src.gui_scene import QCustomGraphicsScene
from src.gui_toolbar import ToolBar
from src.gui_view import QCustomGraphicsView


class Gui(QMainWindow):
    def __init__(self, client):  # noqa: PLR0915
        super().__init__()
        self._vivo = True
        self.client = client
        # Inicializar tema lo antes posible para uso en setup inicial
        self._theme = "light"
        self.client_by_id = {}
        self.transmisor = ClientNullTransmisor()
        self.conexion = None
        self.w = None
        self.ventana_conectar = None
        self.setWindowTitle("PyTeg")
        # self.setFixedSize(QSize(800, 600))
        self.resize(QSize(1280, 800))
        self.setMinimumSize(QSize(800, 600))
        self.setMouseTracking(True)

        # Initialize turn number and current player info
        self._turno_actual = 0
        self._jugador_actual_id = None
        self._jugador_actual_nombre = None
        self._jugador_actual_color = None

        self.colores = Colores()

        self.setup_graphics_view()

        # Create a status bar with permanent widgets for turn number and status
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(26)
        # Aplicar tema al status bar (ya existe self._theme)
        self._apply_statusbar_theme()

        # Add a widget for the current player with color indicator and nickname
        self.jugador_actual_widget = QWidget()
        self.jugador_actual_layout = QHBoxLayout(self.jugador_actual_widget)
        self.jugador_actual_layout.setContentsMargins(4, 0, 4, 0)
        self.jugador_actual_layout.setSpacing(6)

        # Color indicator (square)
        self.color_indicator = QLabel()
        self.color_indicator.setFixedSize(16, 16)
        self.color_indicator.setStyleSheet("""
            background-color: #cccccc;
            border: 1px solid #999999;
            border-radius: 2px;
        """)
        self.jugador_actual_layout.addWidget(self.color_indicator)

        # Turn and player info
        self.turno_label = QLabel("Turno: 0")
        self.turno_label.setStyleSheet("font-weight: 600;")
        self.jugador_actual_layout.addWidget(self.turno_label)

        self.status_bar.addPermanentWidget(self.jugador_actual_widget)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep1)

        # Add a widget for "My Player" info
        self.mi_jugador_widget = QWidget()
        self.mi_jugador_layout = QHBoxLayout(self.mi_jugador_widget)
        self.mi_jugador_layout.setContentsMargins(4, 0, 4, 0)
        self.mi_jugador_layout.setSpacing(6)

        # "Mi jugador:" label
        self.mi_jugador_text = QLabel("Mi jugador:")
        self.mi_jugador_text.setStyleSheet("color: #555;")
        self.mi_jugador_layout.addWidget(self.mi_jugador_text)

        # My color indicator (square)
        self.mi_color_indicator = QLabel()
        self.mi_color_indicator.setFixedSize(16, 16)
        self.mi_color_indicator.setStyleSheet("""
            background-color: #cccccc;
            border: 1px solid #999999;
            border-radius: 2px;
        """)
        self.mi_jugador_layout.addWidget(self.mi_color_indicator)

        # My username
        self.mi_username_label = QLabel("[No conectado]")
        self.mi_username_label.setStyleSheet("font-weight: 600;")
        self.mi_jugador_layout.addWidget(self.mi_username_label)

        self.status_bar.addPermanentWidget(self.mi_jugador_widget)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep2)

        # Add a label for the game state
        self.estado_label = QLabel("Estado: Desconectado")
        self.estado_label.setObjectName("estadoLabel")
        self.estado_label.setProperty("class", "pill")
        self.status_bar.addPermanentWidget(self.estado_label)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep3)

        # Add a label for country selection
        self.seleccion_label = QLabel("Selección: Ninguna")
        self.seleccion_label.setProperty("class", "pill")
        self.status_bar.addPermanentWidget(self.seleccion_label)

        # Add a stretch to push the status message to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_bar.addPermanentWidget(spacer)

        self.setStatusBar(self.status_bar)

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def setup_graphics_view(self):
        # Inicializar componentes principales
        self._setup_chat_and_toolbar()
        self._setup_scene_and_view()

        # Crear splitters y layout principal
        vertical_splitter = self._create_vertical_splitter()
        horizontal_splitter = self._create_horizontal_splitter(vertical_splitter)

        # Configurar columna derecha
        right_column = self._setup_right_column()
        horizontal_splitter.addWidget(right_column)

        # Configurar el layout principal
        self._setup_main_layout(horizontal_splitter)

    def _setup_chat_and_toolbar(self):
        # Agrego el Chat
        self.chat = Chat(self)
        self.chat.show()

        # Agrego la barra de herramientas
        self.toolbar = ToolBar("My main toolbar", self)
        self.addToolBar(self.toolbar)

    def _setup_scene_and_view(self):
        # Agrego la escena y la vista
        self.scene = QCustomGraphicsScene(self)
        self.view = QCustomGraphicsView(self.scene, self)

    def _create_vertical_splitter(self):
        # Create a splitter to hold the QGraphicsView and Chat
        vertical_splitter = QSplitter()
        vertical_splitter.setOrientation(Qt.Vertical)
        vertical_splitter.addWidget(self.view)
        vertical_splitter.addWidget(self.chat)
        vertical_splitter.setStretchFactor(0, 9)  # 90% for QGraphicsView
        vertical_splitter.setStretchFactor(1, 1)  # 10% for Chat
        return vertical_splitter

    def _create_horizontal_splitter(self, vertical_splitter):
        # Create a horizontal splitter to hold the vertical splitter
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Horizontal)
        horizontal_splitter.addWidget(vertical_splitter)
        return horizontal_splitter

    def _setup_right_column(self):
        # Create a placeholder widget for the right column
        right_column = QWidget()
        right_column_layout = QVBoxLayout()
        right_column_layout.setContentsMargins(10, 15, 10, 10)
        right_column_layout.setSpacing(8)

        # Añadir título y lista de jugadores
        self._add_players_title(right_column_layout)
        self._setup_players_list(right_column_layout)

        # Add a spacer to separate the player list from the values
        right_column_layout.addStretch()

        # Add the 6 values below the player list
        self._setup_continent_values(right_column_layout)

        # Configurar el layout de la columna derecha
        right_column.setLayout(right_column_layout)
        return right_column

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
        self.value_labels = {}
        self._row_widgets = {}
        self._last_units = {}

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
        self._row_widgets["Misiles"].setVisible(False)

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
        self._apply_units_theme(section)

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
        self.value_labels[key] = label
        self._row_widgets[key] = row
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
        # Crear un contenedor para la lista de jugadores sin scroll
        players_container = QWidget()
        players_layout = QVBoxLayout(players_container)
        players_layout.setContentsMargins(0, 0, 0, 0)
        players_layout.setSpacing(6)

        # Add a list of players to the right column
        self.player_labels = []
        self._create_player_widgets(players_layout)

        # Añadir un espaciador al final de la lista de jugadores
        players_layout.addStretch()

        # Añadir el contenedor al layout principal
        layout.addWidget(players_container)

    def _create_player_widgets(self, layout):
        # Inicializar lista vacía - se crearán dinámicamente
        self.players_layout = layout

    def _setup_main_layout(self, horizontal_splitter):
        # Create a widget to hold the QGraphicsView and input area
        self.main_widget = QWidget(self)
        main_layout = QGridLayout()
        main_layout.addWidget(horizontal_splitter, 0, 0)
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)

        # Configurar factores de estiramiento para el splitter horizontal
        horizontal_splitter.setStretchFactor(0, 8)  # 80% for the left side
        horizontal_splitter.setStretchFactor(1, 2)  # 20% for the right column

        # Asegurar que la vista se muestre
        self.view.show()

    def update_player_list(self, players):
        """
        Updates the player list on the right column.
        Only shows players that are actually playing.
        :param players: List of tuples (name, color) where color is a QColor.
        """
        # Limpiar widgets existentes
        self._clear_player_widgets()

        # Crear widgets solo para jugadores activos
        for name, color in players:
            self._create_single_player_widget(name, color)

    def _clear_player_widgets(self):
        """Elimina todos los widgets de jugadores existentes"""
        if hasattr(self, "player_labels"):
            for _label, _turn_indicator, player_widget in self.player_labels:
                player_widget.setParent(None)
                player_widget.deleteLater()
        self.player_labels = []

    def _create_single_player_widget(self, name, color):
        """Crea un widget individual para un jugador"""
        # Crear un widget para el jugador (estilo tarjeta, neutro)
        player_widget = QFrame()
        player_widget.setObjectName("playerCard")

        player_layout = QHBoxLayout(player_widget)
        player_layout.setContentsMargins(8, 8, 8, 8)
        player_layout.setSpacing(8)

        # Indicador de color (círculo + glifo inicial)
        turn_indicator = self._make_circle_icon(color.name(), None)
        player_layout.addWidget(turn_indicator)

        # Etiqueta con el nombre del jugador
        label = QLabel(name)
        player_layout.addWidget(label)

        # Estilos unificados con sección UNIDADES
        label.setStyleSheet("color: #333; font-weight: 600; font-size: 13px;")

        # Guardar referencia
        self.player_labels.append((label, turn_indicator, player_widget))

        # Añadir al layout
        self.players_layout.addWidget(player_widget)

        # Aplicar estilo de tarjeta mediante tema
        self._apply_players_theme(player_widget)

    def abrir_ventana_conectar(self):
        # Cancelar selección al abrir ventana de conexión
        if hasattr(self.scene, "selection_manager"):
            self.scene.selection_manager.cancelar_seleccion()
        self.ventana_conectar = None
        self.ventana_conectar = VentanaConectar(self)
        self.ventana_conectar.show()

    def ventana_admin(self):
        self.w = None
        self.w = VentanaAdmin(self)
        self.w.show()

    def ventana_esperar_jugadores(self):
        print("=== Iniciando ventana_esperar_jugadores ===")
        print("Creando nueva ventana de espera...")
        self.w = VentanaEsperarJugadores(self)

        # Conectar la señal de cierre para limpiar la referencia
        def limpiar_ventana():
            print("Limpiando referencia a la ventana de espera")
            if hasattr(self, "w"):
                with contextlib.suppress(Exception):
                    # Desconectar todas las señales para evitar llamadas duplicadas
                    self.w.destroyed.disconnect()

                self.w = None

        self.w.destroyed.connect(limpiar_ventana)

        # Mostrar la ventana
        self.w.show()
        print("Ventana de espera mostrada")

    def update_turno(
        self,
        num_turno,
        num_ronda,
        jugador_actual_id=None,
        jugador_actual_nombre=None,
        jugador_actual_color=None,
    ):
        """Update the turn and round number display.

        Args:
            num_turno (int): The current turn number
            num_ronda (int): The current round number
            jugador_actual_id (int, optional): ID del jugador actual
            jugador_actual_nombre (str, optional): Nombre del jugador actual
            jugador_actual_color (str, optional): Color del jugador actual
        """
        self._turno_actual = num_turno
        self._jugador_actual_id = jugador_actual_id
        self._jugador_actual_nombre = jugador_actual_nombre
        self._jugador_actual_color = jugador_actual_color

        # Actualizar el texto del turno
        if jugador_actual_nombre:
            self.turno_label.setText(
                f"Ronda: {num_ronda} - Turno: {jugador_actual_nombre}"
            )
        else:
            self.turno_label.setText(f"Ronda: {num_ronda} - Turno: {num_turno + 1}")

        # Actualizar el indicador de color
        if jugador_actual_color:
            self.color_indicator.setStyleSheet(f"""
                background-color: {jugador_actual_color};
                border: 1px solid #999999;
                border-radius: 2px;
            """)
        else:
            self.color_indicator.setStyleSheet("""
                background-color: #cccccc;
                border: 1px solid #999999;
                border-radius: 2px;
            """)

    def update_status_bar(self, text, color=None):
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
            color (str, optional): Color for the text (e.g., 'green', 'red', '#ff0000')
        """
        # Apply color styling if provided
        if color:
            # Create a temporary label to apply color styling
            if not hasattr(self, "_status_temp_label"):
                self._status_temp_label = QLabel()
                self.status_bar.addWidget(self._status_temp_label)

            self._status_temp_label.setText(text)
            self._status_temp_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            # Clear the default message to avoid duplication
            self.status_bar.clearMessage()
        else:
            # Use default status bar message
            if hasattr(self, "_status_temp_label"):
                self._status_temp_label.setText("")
            self.status_bar.showMessage(text)

    def clear_status_bar(self):
        """Clear the status bar message, but keep the turn number."""
        self.status_bar.clearMessage()
        # Also clear the temporary colored label if it exists
        if hasattr(self, "_status_temp_label"):
            self._status_temp_label.setText("")

    # ==== Theming & Accessibility ====
    def set_theme(self, theme: str):
        """Cambia el tema de la interfaz ("light" o "dark")."""
        if theme not in {"light", "dark"}:
            return
        self._theme = theme
        # Aplicar tema global a toda la app (fondos, textos, menús, etc.)
        self._apply_global_theme()
        self._apply_statusbar_theme()
        # Reaplicar estilos en secciones
        self._apply_units_theme()
        # Reaplicar estilos tarjetas jugadores
        for _, _, w in getattr(self, "player_labels", []):
            self._apply_players_theme(w)
        # Notificar a la toolbar para actualizar el botón de tema
        if hasattr(self, "toolbar") and hasattr(self.toolbar, "on_theme_changed"):
            self.toolbar.on_theme_changed(self._theme)

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro y aplica el cambio."""
        current = getattr(self, "_theme", "light")
        new_theme = "dark" if current != "dark" else "light"
        self.set_theme(new_theme)

    def _apply_statusbar_theme(self):
        if self._theme == "dark":
            self.status_bar.setStyleSheet(
                """
                QStatusBar { background: #2b2f36; border-top: 1px solid #3a3f47; }
                QStatusBar QLabel { color: #e6e6e6; font-size: 12px; }
                QLabel[class="pill"] {
                    background: #3a3f47; border: 1px solid #4a5060;
                    border-radius: 10px; padding: 2px 8px; color: #e6e6e6;
                }
                QFrame { color: #e6e6e6; }
                """
            )
        else:
            self.status_bar.setStyleSheet(
                """
                QStatusBar { background: #f7f7f9; border-top: 1px solid #e1e3e8; }
                QStatusBar QLabel { color: #333; font-size: 12px; }
                QLabel[class="pill"] {
                    background: #eef1f7; border: 1px solid #d7dbe6;
                    border-radius: 10px; padding: 2px 8px;
                }
                QFrame { color: #333; }
                """
            )

    def _apply_global_theme(self):
        """Aplica un stylesheet global para tema claro/oscuro en toda la ventana."""
        app = QApplication.instance()
        if app is None:
            return
        if getattr(self, "_theme", "light") == "dark":
            app.setStyleSheet(
                "QWidget { background-color: #1e1f23; color: #e6e6e6; }\n"
                "QToolBar { background-color: #2b2f36; "
                "border-bottom: 1px solid #3a3f47; }\n"
                "QMenu { background-color: #2b2f36; color: #e6e6e6; "
                "border: 1px solid #3a3f47; }\n"
                "QMenu::item:selected { background-color: #3a3f47; }\n"
                "QSplitter::handle { background: #2b2f36; }\n"
                "QLineEdit, QTextEdit, QPlainTextEdit { background: #252a33; "
                "color: #e6e6e6; border: 1px solid #3a3f47; }\n"
                "QListWidget, QTreeWidget, QTableWidget, QScrollArea { "
                "background: #23262b; color: #e6e6e6; }\n"
                "QPushButton { background: #3a3f47; color: #e6e6e6; "
                "border: 1px solid #4a5060; border-radius: 4px; "
                "padding: 4px 8px; }\n"
                "QPushButton:hover { background: #444b5a; }\n"
                "QStatusBar { background: #2b2f36; }\n"
            )
        else:
            # Restaurar estilos por defecto (mantiene estilos locales específicos)
            app.setStyleSheet("")

    def _apply_units_theme(self, root: QWidget | None = None):
        root = root or getattr(self, "centralWidget", lambda: None)()
        theme = getattr(self, "_theme", "light")
        if theme == "dark":
            ss = (
                "#unitsSection { background: #21252b; border: 1px solid #3a3f47;"
                " border-radius: 8px; }\n"
                "#unitsTitle { color: #e6e6e6; font-size: 13px; font-weight: 700; }\n"
                "#unitRowLabel { font-weight: 600; color: #ddd; }\n"
            )
        else:
            ss = (
                "#unitsSection { background: #fafbfe; border: 1px solid #e6e9f2;"
                " border-radius: 8px; }\n"
                "#unitsTitle { color: #333333; font-size: 13px; font-weight: 700; }\n"
                "#unitRowLabel { font-weight: 600; color: #555; }\n"
            )
        # Aplicar al contenedor de la sección si existe
        if root is None:
            return
        # Buscar el QFrame con objectName unitsSection en la jerarquía inmediata
        # En este contexto, "root" es la sección creada arriba
        if isinstance(root, QFrame) and root.objectName() == "unitsSection":
            root.setStyleSheet(ss)

    def _apply_players_theme(self, player_widget: QFrame):
        if self._theme == "dark":
            player_widget.setStyleSheet(
                "#playerCard { background: #272b33; border-radius: 6px;"
                " border: 1px solid #3a3f47; }"
            )
        else:
            player_widget.setStyleSheet(
                "#playerCard { background: #ffffff; border-radius: 6px;"
                " border: 1px solid #e6e9f2; }"
            )

    def update_game_state(self, estado):
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state
        """
        # Traducir estados técnicos a nombres más amigables
        estados_amigables = {
            "INICIAL": "Inicial",
            "EsperarJugadores": "Esperando Jugadores",
            "JUGANDO": "En Juego",
            "FINALIZADO": "Finalizado",
            "Conectado": "Conectado",
            "Desconectado": "Desconectado",
        }

        estado_mostrar = estados_amigables.get(estado, estado)
        self.estado_label.setText(f"Estado: {estado_mostrar}")

    def update_mi_jugador_info(self):
        """Actualiza la información del usuario actual (mi jugador).

        Actualiza la información en la barra de estado.
        """
        try:
            debug_logger.log("GUI: update_mi_jugador_info llamado")
            # Verificar que tenemos un cliente conectado
            if (
                not hasattr(self, "client")
                or not self.client
                or not self.client.userid()
            ):
                debug_logger.log("GUI: No hay cliente conectado")
                self.mi_username_label.setText("[No conectado]")
                self.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
                return

            # Obtener mi usuario ID
            mi_user_id = self.client.userid()
            debug_logger.log(f"GUI: Mi user_id: {mi_user_id}")

            # Obtener mi nombre de usuario
            mi_username = "[Sin nombre]"
            if hasattr(self.client, "username") and self.client.username():
                mi_username = self.client.username()
            debug_logger.log(f"GUI: Mi username: {mi_username}")

            # Obtener mi color asignado
            mi_color = None
            if hasattr(self, "colores") and self.colores:
                mi_color = self.colores.color_asignado(mi_user_id)
                debug_logger.log(f"GUI: Mi color: {mi_color}")

            # Actualizar el nombre de usuario
            self.mi_username_label.setText(mi_username)

            # Actualizar el color
            if mi_color and hasattr(mi_color, "name"):
                color_hex = mi_color.name()  # Obtener color en formato hexadecimal
                debug_logger.log(f"GUI: Color hex: {color_hex}")
                self.mi_color_indicator.setStyleSheet(f"""
                    background-color: {color_hex};
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
            else:
                debug_logger.log("GUI: No hay color asignado, usando color por defecto")
                # Color por defecto si no hay color asignado
                self.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
        except (AttributeError, KeyError, ValueError) as e:
            print(f"Error al actualizar información de mi jugador: {e}")
            self.mi_username_label.setText("[Error]")

    def update_unidades_disponibles(self, unidades):  # noqa: PLR0912
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2, "Africa": 3}
        """
        # Mapeo de nombres de continentes del servidor a los de la GUI
        continent_mapping = {
            "Africa": "África",
            "Europa": "Europa",
            "Asia": "Asia",
            "América del Sur": "América del Sur",
            "América del Norte": "América del Norte",
            "Oceanía": "Oceanía",
        }

        # Actualizar unidades generales (infantería)
        if "infanteria" in unidades:
            cantidad = unidades["infanteria"]
            prev = self._last_units.get("Generales", None)
            # Estilo con color verde si hay unidades disponibles
            if cantidad > 0:
                style = (
                    "font-weight: bold; "
                    "color: #2E7D32; "
                    "background-color: #E8F5E8; "
                    "padding: 4px 8px; "
                    "border-radius: 4px; "
                    "border-left: 3px solid #4CAF50;"
                )
                text = f"Generales: {cantidad}"
            else:
                style = "font-weight: bold; color: #666666;"
                text = f"Generales: {cantidad}"

            self.value_labels["Generales"].setText(text)
            self.value_labels["Generales"].setStyleSheet(style)
            if prev is None or prev != cantidad:
                self._flash_row("Generales")
            self._last_units["Generales"] = cantidad

        # Actualizar unidades de continentes
        for server_name, gui_name in continent_mapping.items():
            if server_name in unidades and gui_name in self.value_labels:
                cantidad = unidades[server_name]
                prev = self._last_units.get(gui_name, None)
                if cantidad > 0:
                    # Estilo destacado para continentes con unidades disponibles
                    style = (
                        "font-weight: bold; "
                        "color: #1565C0; "
                        "background-color: #E3F2FD; "
                        "padding: 4px 8px; "
                        "border-radius: 4px; "
                        "border-left: 3px solid #2196F3;"
                    )
                    text = f"{gui_name}: {cantidad}"
                else:
                    # Estilo normal para continentes sin unidades
                    style = "font-weight: bold; color: #666666;"
                    text = f"{gui_name}: 0"

                self.value_labels[gui_name].setText(text)
                self.value_labels[gui_name].setStyleSheet(style)
                if prev is None or prev != cantidad:
                    self._flash_row(gui_name)
                self._last_units[gui_name] = cantidad
            elif gui_name in self.value_labels:
                # Resetear continentes que no tienen unidades disponibles
                self.value_labels[gui_name].setText(f"{gui_name}: 0")
                self.value_labels[gui_name].setStyleSheet(
                    "font-weight: bold; color: #666666;"
                )

        # Actualizar Misiles: usar fila existente y mostrar/ocultar
        if "misiles" in unidades and unidades["misiles"] > 0:
            text = f"Misiles: {unidades['misiles']}"
            style = (
                "font-weight: bold; "
                "color: #D32F2F; "
                "background-color: #FFEBEE; "
                "padding: 4px 8px; "
                "border-radius: 4px; "
                "border-left: 3px solid #F44336;"
            )
            self.value_labels["Misiles"].setText(text)
            self.value_labels["Misiles"].setStyleSheet(style)
            # Mostrar fila completa (parent del label)
            self._row_widgets["Misiles"].setVisible(True)
            prev = self._last_units.get("Misiles", None)
            if prev is None or prev != unidades["misiles"]:
                self._flash_row("Misiles")
            self._last_units["Misiles"] = unidades["misiles"]
        else:
            # Ocultar y resetear
            self.value_labels["Misiles"].setText("Misiles: 0")
            self.value_labels["Misiles"].setStyleSheet(
                "font-weight: bold; color: #666666;"
            )
            self._row_widgets["Misiles"].setVisible(False)
            self._last_units["Misiles"] = 0

    def _flash_row(self, key: str):
        """Aplica un highlight temporal a la fila cuando cambian valores."""
        row = self._row_widgets.get(key)
        if not row:
            return
        original = row.styleSheet()
        row.setStyleSheet(original + "\n#unitRow { background: #fff8e1; }")
        QTimer.singleShot(300, lambda: row.setStyleSheet(original))

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.chat.send_message()
        elif event.key() == Qt.Key_Escape and hasattr(self.scene, "selection_manager"):
            # Cancelar selección con tecla Escape usando selection_manager
            self.scene.selection_manager.cancelar_seleccion()

    def closeEvent(self, _):  # noqa: N802
        self._vivo = False

    def finalizar_turno(self):
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        # Aquí puedes agregar la lógica para finalizar el turno actual
        # Por ejemplo, notificar al servidor que el turno ha terminado
        if hasattr(self, "transmisor") and hasattr(self.transmisor, "finalizar_turno"):
            self.transmisor.finalizar_turno()
            # Cancelar selección después de finalizar turno
            if hasattr(self.scene, "selection_manager"):
                self.scene.selection_manager.cancelar_seleccion()
        else:
            print("No se pudo finalizar el turno: transmisor no disponible")

    def atacar(self):
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        # Verificar que tenemos un selection_manager
        if not hasattr(self.scene, "selection_manager"):
            self.update_status_bar(
                "Error: No hay sistema de selección disponible", "red"
            )
            return

        selection_manager = self.scene.selection_manager
        origen = selection_manager.get_pais_origen()
        destino = selection_manager.get_pais_destino()

        if not origen:
            self.update_status_bar("Selecciona un país de origen primero", "orange")
            return

        if not destino:
            self.update_status_bar(
                "Selecciona un país de destino después del origen", "orange"
            )
            return

        if hasattr(self, "transmisor") and hasattr(self.transmisor, "atacar"):
            # Obtener información del país atacante para determinar unidades disponibles
            max_unidades = self.get_max_attack_units(origen)

            if max_unidades < 1:
                self.update_status_bar(
                    f"No hay suficientes unidades en {origen} para atacar", "orange"
                )
                return

            # Mostrar diálogo para seleccionar cantidad de unidades
            dialog = AttackDialog(origen, destino, max_unidades, self)
            if dialog.exec() == QDialog.Accepted:
                cantidad_unidades = dialog.get_cantidad_unidades()
                self.transmisor.atacar(origen, destino, cantidad_unidades)
                self.update_status_bar(
                    f"Atacando de {origen} a {destino} con {cantidad_unidades} "
                    f"unidad{'es' if cantidad_unidades > 1 else ''}...",
                    "blue",
                )
                # Cancelar selección después de atacar
                selection_manager.cancelar_seleccion()
        else:
            self.update_status_bar("Error: No hay conexión disponible", "red")

    def get_max_attack_units(self, pais):
        """
        Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)
        """
        # Buscar el país en la escena para obtener sus unidades
        if hasattr(self.scene, "paises") and pais in self.scene.paises:
            pais_widget = self.scene.paises[pais]
            unidades_totales = pais_widget.get_unidades()
            # Se necesita dejar al menos 1 unidad en el país
            unidades_disponibles = max(0, unidades_totales - 1)
            # Máximo 3 unidades para atacar
            return min(unidades_disponibles, 3)

        # Si no se encuentra el país, asumir 0 unidades disponibles
        return 0
