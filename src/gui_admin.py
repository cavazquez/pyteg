from PySide6.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QWidget,
)


class VentanaAdmin(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        layout = QVBoxLayout()
        boton = QPushButton("Empezar")
        layout.addWidget(boton)
        self.setLayout(layout)
