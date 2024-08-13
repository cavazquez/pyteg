from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.client_transmisor import ClientNullTransmisor
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
        self.transmisor = ClientNullTransmisor()
        self.conexion = None
        self.w = None
        self.ventana_conectar = None
        self.setWindowTitle("PyTeg")
        self.setFixedSize(QSize(1024, 768))
        self.setMouseTracking(True)

        self.color = None
        self.colores = []

        self.setup_graphics_view()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def setup_graphics_view(self):
        input_layout = QVBoxLayout()

        self.chat = Chat(self)
        self.chat.show()
        input_layout.addWidget(self.chat)

        toolbar = ToolBar("My main toolbar", self)
        self.addToolBar(toolbar)

        # self.scene = QGraphicsScene()
        self.scene = QCustomGraphicsScene(self)
        self.view = QCustomGraphicsView(self.scene, self)

        # Create a widget to hold the QGraphicsView and input area
        self.main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(input_layout)
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
