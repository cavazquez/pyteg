from PySide6.QtCore import QSize
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.client_connection import ConnectionClient


class VentanaConectar(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

        layout = QVBoxLayout()
        self.setWindowTitle("Conectar")
        self.setFixedSize(QSize(300, 150))

        # Crear widget
        self.label_addr = QLabel("Direccion")
        self.addr = QLineEdit("localhost")
        self.label_port = QLabel("Puerto")
        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator())
        button_conectar = QPushButton("Conectar")
        button_conectar.clicked.connect(self.connect)

        # Agregar widget al layout
        layout.addWidget(self.label_addr)
        layout.addWidget(self.addr)
        layout.addWidget(self.label_port)
        layout.addWidget(self.port)
        layout.addWidget(button_conectar)

        self.setLayout(layout)

    def connect(self):
        try:
            addr = self.addr.text()
            port = int(self.port.text())
            self._conexion = ConnectionClient(self._main_window, addr, port)
            self._conexion.conectar()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {e!s}")
