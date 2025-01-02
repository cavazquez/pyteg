from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTextEdit,
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
        self.setFixedSize(QSize(800, 600))
        self.setMouseTracking(True)

        self.colores = Colores()

        self.setup_graphics_view()

        self.status_bar = QStatusBar()
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
        vertical_splitter.setStretchFactor(0, 7)  # 70% for QGraphicsView
        vertical_splitter.setStretchFactor(1, 3)  # 30% for Chat

        # Create a horizontal splitter to
        # hold the vertical splitter and the right column
        horizontal_splitter = QSplitter()
        horizontal_splitter.setOrientation(Qt.Horizontal)
        horizontal_splitter.addWidget(vertical_splitter)

        # Create a placeholder widget for the
        # right column
        right_column = QWidget()
        right_column_layout = QVBoxLayout()
        right_column.setLayout(right_column_layout)
        horizontal_splitter.addWidget(right_column)
        horizontal_splitter.setStretchFactor(0, 7)  # 70% for the left side
        horizontal_splitter.setStretchFactor(1, 3)  # 30% for the right column

        # Add a QTextEdit to the right column
        text_box = QTextEdit()
        right_column_layout.addWidget(text_box)

        # Create a widget to hold the QGraphicsView and input area
        self.main_widget = QWidget(self)
        main_layout = QGridLayout()
        main_layout.addWidget(horizontal_splitter, 0, 0)
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)
        self.view.show()

    def abrir_ventana_conectar(self):
        self.ventana_conectar = None
        self.ventana_conectar = VentanaConectar(self)
        self.ventana_conectar.show()

    def ventana_admin(self):
        self.w = None
        self.w = VentanaAdmin(self)
        self.w.show()

    def ventana_esperar_jugadores(self):
        self.w = None
        self.w = VentanaEsperarJugadores(self)
        self.w.show()

    def update_status_bar(self, text):
        self.status_bar.showMessage(text)

    def clear_status_bar(self):
        self.status_bar.clearMessage()

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.chat.send_message()

    def closeEvent(self, _):  # noqa: N802
        self._vivo = False
