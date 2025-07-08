import contextlib

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.client_transmisor import ClientNullTransmisor
from src.cliente_colores import Colores
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

        # Initialize turn number
        self._turno_actual = 0

        self.colores = Colores()

        self.setup_graphics_view()

        # Create a status bar with permanent widgets for turn number and status message
        self.status_bar = QStatusBar()

        # Add a label for the turn number that stays on the left
        self.turno_label = QLabel("Turno: 0")
        self.status_bar.addPermanentWidget(self.turno_label)

        # Add a stretch to push the status message to the right
        self.status_bar.addPermanentWidget(QLabel(""))

        self.setStatusBar(self.status_bar)

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def setup_graphics_view(self):
        # Agrego el Chat
        self.chat = Chat(self)
        self.chat.show()

        # Agrego la barra de herramientas
        toolbar = ToolBar("My main toolbar", self)
        self.addToolBar(toolbar)

        # Agrego la escena y la vista
        self.scene = QCustomGraphicsScene(self)
        self.view = QCustomGraphicsView(self.scene, self)

        # Create a splitter to hold the QGraphicsView and Chat
        vertical_splitter = QSplitter()
        vertical_splitter.setOrientation(Qt.Vertical)
        vertical_splitter.addWidget(self.view)
        vertical_splitter.addWidget(self.chat)
        vertical_splitter.setStretchFactor(0, 9)  # 90% for QGraphicsView
        vertical_splitter.setStretchFactor(1, 1)  # 10% for Chat

        # Create a horizontal splitter to hold the vertical splitter
        # and the right column
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Horizontal)
        horizontal_splitter.addWidget(vertical_splitter)

        # Create a placeholder widget for the right column
        right_column = QWidget()
        right_column_layout = QVBoxLayout()

        # Add a list of players to the right column
        self.player_labels = []
        for i in range(8):  # Max 8 players
            label = QLabel(f"Jugador {i + 1}: [Sin asignar]")
            label.setStyleSheet("color: gray;")  # Default color
            right_column_layout.addWidget(label)
            self.player_labels.append(label)

        # Add a spacer to separate the player list from the values
        right_column_layout.addStretch()

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
            right_column_layout.addWidget(label)
            self.value_labels[value] = label

        right_column.setLayout(right_column_layout)
        horizontal_splitter.addWidget(right_column)
        horizontal_splitter.setStretchFactor(0, 8)  # 80% for the left side
        horizontal_splitter.setStretchFactor(1, 2)  # 20% for the right column

        # Create a widget to hold the QGraphicsView and input area
        self.main_widget = QWidget(self)
        main_layout = QGridLayout()
        main_layout.addWidget(horizontal_splitter, 0, 0)
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)
        self.view.show()

    def update_player_list(self, players):
        """
        Updates the player list on the right column.
        :param players: List of tuples (name, color) where color is a QColor.
        """
        for i, (name, color) in enumerate(players):
            if i < len(self.player_labels):
                # Calcular el contraste para el texto basado
                # en la luminosidad del color de fondo
                # Fórmula de luminosidad relativa:
                # 0.299*R + 0.587*G + 0.114*B
                r, g, b = color.red(), color.green(), color.blue()
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                text_color = "white" if brightness < 0.6 else "black"

                # Establecer estilo con fondo ligeramente
                # oscuro y borde para mejor contraste
                self.player_labels[i].setText(f"Jugador {i + 1}: {name}")
                self.player_labels[i].setStyleSheet(
                    f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {color.name()};
                        padding: 4px;
                        border-radius: 4px;
                        border: 1px solid #333;
                        margin: 1px;
                    }}
                    """
                )
        # Clear remaining labels if fewer than 8 players
        for j in range(len(players), len(self.player_labels)):
            self.player_labels[j].setText(f"Jugador {j + 1}: [Sin asignar]")
            self.player_labels[j].setStyleSheet(
                """
                QLabel {
                    color: #CCCCCC;
                    background-color: #333333;
                    padding: 4px;
                    border-radius: 4px;
                    border: 1px solid #555555;
                    margin: 1px;
                }
                """
            )

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

    def update_turno(self, num_turno, num_ronda):
        """Update the turn and round number display.

        Args:
            num_turno (int): The current turn number
            num_ronda (int): The current round number
        """
        self._turno_actual = num_turno
        self.turno_label.setText(f"Ronda: {num_ronda} - Turno: {num_turno + 1}")

    def update_status_bar(self, text):
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
        """
        # Update the status message (temporary message on the right)
        self.status_bar.showMessage(text)

    def clear_status_bar(self):
        """Clear the status bar message, but keep the turn number."""
        self.status_bar.clearMessage()

    def update_unidades_disponibles(self, unidades):
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2}
        """
        # Actualizar la etiqueta de Generales con las unidades de infantería
        if "infanteria" in unidades:
            self.value_labels["Generales"].setText(
                f"Generales: {unidades['infanteria']}"
            )

        # Actualizar la etiqueta de Misiles si está disponible
        if "misiles" in unidades and unidades["misiles"] > 0:
            # Buscar si ya existe una etiqueta para misiles
            if not hasattr(self, "misiles_label"):
                # Insertar después de Generales
                layout = self.value_labels["Generales"].parent().layout()
                index = layout.indexOf(self.value_labels["Generales"]) + 1

                self.misiles_label = QLabel(f"Misiles: {unidades['misiles']}")
                self.misiles_label.setStyleSheet("font-weight: bold;")
                layout.insertWidget(index, self.misiles_label)
            else:
                self.misiles_label.setText(f"Misiles: {unidades['misiles']}")
        elif hasattr(self, "misiles_label"):
            # Si no hay misiles disponibles, eliminar la etiqueta
            self.misiles_label.deleteLater()
            del self.misiles_label

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.chat.send_message()

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
