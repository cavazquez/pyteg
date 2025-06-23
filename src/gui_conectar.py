from PySide6.QtCore import QSize
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.client_connection import ConnectionClient


class VentanaConectar(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

        layout = QVBoxLayout()
        self.setWindowTitle("Conectar")
        self.setFixedSize(QSize(300, 150))

        # Crear widget
        self.label_addr = QLabel("Dirección:")
        self.addr = QLineEdit("localhost")
        self.label_port = QLabel("Puerto:")
        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator())
        self.label_username = QLabel("Nombre de usuario:")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Ingresa tu nombre de usuario")
        button_conectar = QPushButton("Conectar")
        button_conectar.clicked.connect(self.connect)

        # Agregar widget al layout
        layout.addWidget(self.label_addr)
        layout.addWidget(self.addr)
        layout.addWidget(self.label_port)
        layout.addWidget(self.port)
        layout.addWidget(self.label_username)
        layout.addWidget(self.username)
        layout.addWidget(button_conectar)

        # Ajustar el tamaño de la ventana para el nuevo campo
        self.setFixedSize(QSize(300, 200))

        self.setLayout(layout)

    def connect(self):
        try:
            addr = self.addr.text()
            port = int(self.port.text())
            username = self.username.text().strip()

            if not username:
                QMessageBox.warning(
                    self, "Error", "Por favor ingresa un nombre de usuario"
                )
                return

            self._conexion = ConnectionClient(self._main_window, addr, port, username)
            self._conexion.conectar()
            self.accept()  # Cerrar el diálogo si la conexión es exitosa

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {e!s}")
