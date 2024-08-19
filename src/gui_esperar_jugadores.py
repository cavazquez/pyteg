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
        colores = self._main_window.colores.colores()
        for i in range(6):
            color = colores[i]
            radio = QRadioButton("    ", self)
            radio.setStyleSheet(f"background-color: {color.name()};")
            fila = i // 2
            columna = i % 2
            grid_layout.addWidget(radio, fila, columna)

        colores_asignados = self._main_window.colores.colores_asignados()
        print(colores_asignados)

        layout.addLayout(grid_layout)
        self.setLayout(layout)
