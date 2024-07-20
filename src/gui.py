from PySide6.QtCore import QSize, QThreadPool
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.gui_chat import Chat
from src.gui_conectar import VentanaConectar
from src.gui_scene import QCustomGraphicsScene
from src.gui_view import QCustomGraphicsView


class Gui(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self._vivo = True
        self.client = client
        self.threadpool = QThreadPool()
        self.w = None
        self.setWindowTitle("PyTeg")
        self.setFixedSize(QSize(1024, 768))
        self.setMouseTracking(True)

        self.setup_graphics_view()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def setup_graphics_view(self):
        input_layout = QVBoxLayout()

        self.chat = Chat(self.client)
        self.chat.show()
        input_layout.addWidget(self.chat)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        button_conectar = QAction("Conectar", self)
        button_conectar.triggered.connect(self.ventana_conectar)
        toolbar.addAction(button_conectar)
        button_agregar_5 = QAction("Agregar 5", self)
        button_agregar_5.triggered.connect(self.agregar_5)
        toolbar.addAction(button_agregar_5)

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

    def ventana_conectar(self):
        self.w = None
        self.w = VentanaConectar(self)
        self.w.show()

    def agregar_5(self):
        pass

    def update_unidades(self, pais, cantidad):
        pass

    def send_message(self):
        text = self.input_field.text()
        if text:
            self.client.send_chat(text)
            self.input_field.clear()

    def update_status_bar(self, text):
        self.status_bar.showMessage(text)

    def clear_status_bar(self):
        self.status_bar.clearMessage()

    def msg_chat(self, text):
        self.chat.append(text)

    def close_event(self, event):
        self._vivo = False
        print(event)
        self.client.cerrar()
        print("Aceptando Evento")
        event.accept()
