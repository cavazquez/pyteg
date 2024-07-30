from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.client_receptor import Receptor
from src.client_transmisor import ClientTransmisor
from src.client_connection import ConnectionClient


class VentanaConectar(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        layout = QVBoxLayout()
        self.setWindowTitle("Conectar")
        self.setFixedSize(QSize(300, 150))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)
        label_addr = QLabel("Direccion")
        addr = QLineEdit("localhost")
        label_port = QLabel("Puerto")
        port = QLineEdit("65432")
        port.setValidator(QIntValidator())
        button_conectar = QPushButton("Conectar")
        button_conectar.clicked.connect(self.connect)
        layout.addWidget(label_addr)
        layout.addWidget(addr)
        layout.addWidget(label_port)
        layout.addWidget(port)
        layout.addWidget(button_conectar)
        self.setLayout(layout)

    def connect(self):
        try:
            self._conexion = ConnectionClient()
            self._conexion.conectar()
            print(f"self._conexion {self._conexion}")
            self._main_window.threadpool.start(
                Receptor(
                    self._main_window.client,
                    self._main_window,
                    self._conexion,
                ),
            )
            self._main_window.transmisor = ClientTransmisor(self._conexion)
        except ConnectionRefusedError:
            QMessageBox.warning(self, "Advertencia", "conexión rehusada.")
        finally:
            self.close()
