from PySide6.QtWidgets import (
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

        self.button = QPushButton("Empezar")
        self.button.clicked.connect(self.empezar)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def empezar(self):
        self.main_window.transmisor.empezar()
        self.close()
