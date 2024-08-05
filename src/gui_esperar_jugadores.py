from PySide6.QtWidgets import (
    QGridLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class VentanaEsperarJugadores(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        self.inicializar_ui()

    def inicializar_ui(self):
        self.setWindowTitle("Esperando jugadores")

        layout = QVBoxLayout()

        grid_layout = QGridLayout()

        # Crear 6 botones como opciones
        for i in range(6):
            radio = QRadioButton(f"Opción {i}", self)
            fila = i // 2
            columna = i % 2
            grid_layout.addWidget(radio, fila, columna)

        layout.addLayout(grid_layout)
        self.setLayout(layout)
