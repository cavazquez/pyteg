import contextlib

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.client_transmisor import ClientNullTransmisor
from src.cliente_colores import Colores
from src.debug_logger import debug_logger
from src.gui_admin import VentanaAdmin
from src.gui_chat import Chat
from src.gui_conectar import VentanaConectar
from src.gui_esperar_jugadores import VentanaEsperarJugadores
from src.gui_scene import QCustomGraphicsScene
from src.gui_toolbar import ToolBar
from src.gui_view import QCustomGraphicsView


class Gui(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self._vivo = True
        self.client = client
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

        # Create a status bar with permanent widgets for turn number and status message
        self.status_bar = QStatusBar()

        # Add a widget for the current player with color indicator and nickname
        self.jugador_actual_widget = QWidget()
        self.jugador_actual_layout = QHBoxLayout(self.jugador_actual_widget)
        self.jugador_actual_layout.setContentsMargins(0, 0, 0, 0)
        self.jugador_actual_layout.setSpacing(5)

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
        self.jugador_actual_layout.addWidget(self.turno_label)

        self.status_bar.addPermanentWidget(self.jugador_actual_widget)

        # Add a widget for "My Player" info
        self.mi_jugador_widget = QWidget()
        self.mi_jugador_layout = QHBoxLayout(self.mi_jugador_widget)
        self.mi_jugador_layout.setContentsMargins(0, 0, 0, 0)
        self.mi_jugador_layout.setSpacing(5)

        # "Mi jugador:" label
        self.mi_jugador_text = QLabel("Mi jugador:")
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
        self.mi_jugador_layout.addWidget(self.mi_username_label)

        self.status_bar.addPermanentWidget(self.mi_jugador_widget)

        # Add a label for the game state
        self.estado_label = QLabel("Estado: Desconectado")
        self.status_bar.addPermanentWidget(self.estado_label)

        # Add a label for country selection
        self.seleccion_label = QLabel("Selección: Ninguna")
        self.status_bar.addPermanentWidget(self.seleccion_label)

        # Add a stretch to push the status message to the right
        self.status_bar.addPermanentWidget(QLabel(""))

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
        toolbar = ToolBar("My main toolbar", self)
        self.addToolBar(toolbar)

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
        # Add the 6 values below the player list
        self.value_labels = {}
        values = [
            "Generales",
            "América del Sur",
            "América del Norte",
            "Europa",
            "Asia",
            "África",
        ]
        for value in values:
            label = QLabel(f"{value}: 0")  # Default value is 0
            label.setStyleSheet("font-weight: bold;")  # Make the text bold
            layout.addWidget(label)
            self.value_labels[value] = label

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
        # Crear un widget para el jugador
        player_widget = QFrame()
        player_widget.setFrameShape(QFrame.StyledPanel)
        player_widget.setFrameShadow(QFrame.Raised)

        player_layout = QHBoxLayout(player_widget)
        player_layout.setContentsMargins(8, 8, 8, 8)
        player_layout.setSpacing(8)

        # Indicador de turno (círculo)
        turn_indicator = QLabel()
        turn_indicator.setFixedSize(12, 12)
        player_layout.addWidget(turn_indicator)

        # Etiqueta con el nombre del jugador
        label = QLabel(name)
        player_layout.addWidget(label)

        # Calcular el contraste para el texto basado en la luminosidad
        # del color de fondo
        r, g, b = color.red(), color.green(), color.blue()
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        text_color = "white" if brightness < 0.6 else "black"

        # Aplicar estilos
        label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 13px;")

        # Estilo del indicador de turno (por ahora todos iguales)
        turn_indicator.setStyleSheet(f"""
            background-color: {color.name()};
            border-radius: 6px;
        """)

        # Estilo del widget del jugador
        player_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid {"#555555" if brightness < 0.6 else "#CCCCCC"};
            }}
        """)

        # Guardar referencia
        self.player_labels.append((label, turn_indicator, player_widget))

        # Añadir al layout
        self.players_layout.addWidget(player_widget)

    def abrir_ventana_conectar(self):
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
        except Exception as e:
            print(f"Error al actualizar información de mi jugador: {e}")
            self.mi_username_label.setText("[Error]")

    def update_unidades_disponibles(self, unidades):
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
                text = f"🪖 Generales: {cantidad}"
            else:
                style = "font-weight: bold; color: #666666;"
                text = f"🪖 Generales: {cantidad}"

            self.value_labels["Generales"].setText(text)
            self.value_labels["Generales"].setStyleSheet(style)

        # Actualizar unidades de continentes
        for server_name, gui_name in continent_mapping.items():
            if server_name in unidades and gui_name in self.value_labels:
                cantidad = unidades[server_name]
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
                    text = f"🌍 {gui_name}: {cantidad}"
                else:
                    # Estilo normal para continentes sin unidades
                    style = "font-weight: bold; color: #666666;"
                    text = f"{gui_name}: 0"

                self.value_labels[gui_name].setText(text)
                self.value_labels[gui_name].setStyleSheet(style)
            elif gui_name in self.value_labels:
                # Resetear continentes que no tienen unidades disponibles
                self.value_labels[gui_name].setText(f"{gui_name}: 0")
                self.value_labels[gui_name].setStyleSheet(
                    "font-weight: bold; color: #666666;"
                )

        # Actualizar la etiqueta de Misiles si está disponible
        if "misiles" in unidades and unidades["misiles"] > 0:
            # Buscar si ya existe una etiqueta para misiles
            if not hasattr(self, "misiles_label"):
                # Insertar después de Generales
                layout = self.value_labels["Generales"].parent().layout()
                index = layout.indexOf(self.value_labels["Generales"]) + 1

                self.misiles_label = QLabel(f"🚀 Misiles: {unidades['misiles']}")
                style = (
                    "font-weight: bold; "
                    "color: #D32F2F; "
                    "background-color: #FFEBEE; "
                    "padding: 4px 8px; "
                    "border-radius: 4px; "
                    "border-left: 3px solid #F44336;"
                )
                self.misiles_label.setStyleSheet(style)
                layout.insertWidget(index, self.misiles_label)
            else:
                self.misiles_label.setText(f"🚀 Misiles: {unidades['misiles']}")
        elif hasattr(self, "misiles_label"):
            # Si no hay misiles disponibles, eliminar la etiqueta
            self.misiles_label.deleteLater()
            del self.misiles_label

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
            self.transmisor.atacar(origen, destino)
            self.update_status_bar(f"Atacando de {origen} a {destino}...", "blue")
        else:
            self.update_status_bar("Error: No hay conexión disponible", "red")
