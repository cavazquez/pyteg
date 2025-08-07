from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class VentanaAdmin(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Admin")

        self.layout = QVBoxLayout()

        # Fila para ingresar los segundos
        self.seconds_row = QHBoxLayout()
        self.seconds_label = QLabel("Segundos:")
        self.seconds_input = QLineEdit()
        self.seconds_input.setPlaceholderText("Ingresar segundos")
        self.seconds_input.setValidator(QIntValidator(0, 3600, self))
        self.seconds_input.setText("0")  # valor por defecto

        self.seconds_row.addWidget(self.seconds_label)
        self.seconds_row.addWidget(self.seconds_input)

        self.layout.addLayout(self.seconds_row)

        self.button = QPushButton("Empezar")
        self.button.clicked.connect(self.empezar)
        # Permitir activar con Enter
        self.button.setDefault(True)
        self.button.setAutoDefault(True)
        self.seconds_input.returnPressed.connect(self.empezar)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def empezar(self):
        # Leer y validar los segundos ingresados
        segundos = None
        if self.seconds_input.text().strip():
            try:
                segundos = int(self.seconds_input.text())
            except ValueError:
                segundos = None

        self.main_window.transmisor.empezar(segundos)
        self.close()
