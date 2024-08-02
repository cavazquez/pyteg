from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)


class VentanaEsperarJugadores(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        layout = QVBoxLayout()
        self.setLayout(layout)
