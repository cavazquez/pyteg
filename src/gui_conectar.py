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


class VentanaConectar(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, client):
        self.client = client
        super().__init__()
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
            self.client.conectar()
            self.close()
        except ConnectionRefusedError:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Advertencia")
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Conexión rehusada.")
            msgBox.setModal(True)
            msgBox.exec()
