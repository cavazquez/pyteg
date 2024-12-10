from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class VentanaEsperarJugadores(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

        self.radio_por_colores = {}
        self.inicializar_ui()
        self.cargar_colores_asignados()

    def inicializar_ui(self):
        self.setWindowTitle("Esperando jugadores")
        self.setFixedSize(QSize(300, 200))

        layout = QVBoxLayout()

        grid_layout = QGridLayout()

        # Crear 6 botones como opciones
        colores = self._main_window.colores.colores()
        for color in colores:
            # Crear un layout horizontal para cada fila
            fila_layout = QHBoxLayout()

            # Crear un widget para mostrar el color
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid black;",
            )

            # Crear el botón de radio
            radio = QRadioButton("           ", self)
            self.radio_por_colores[color.name()] = radio

            # Añadir el color y el botón al layout horizontal
            fila_layout.addWidget(color_label)
            fila_layout.addWidget(radio)

            # Añadir el layout horizontal al layout principal
            layout.addLayout(fila_layout)

        layout.addLayout(grid_layout)
        self.setLayout(layout)

    def cargar_colores_asignados(self):
        colores_asignados = self._main_window.colores.colores_asignados()
        print(colores_asignados)
        for user_id, color in colores_asignados.items():
            print(f"user_id: {user_id} , color: {color}")
            radio = self.radio_por_colores.get(color.name())
            if radio:
                radio.setText(f"{user_id}")
                radio.setEnabled(False)
