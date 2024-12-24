from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui_radio_color import GuiRadioButtonColor


class VentanaEsperarJugadores(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

        self.radio_por_colores = {}
        self.inicializar_ui()
        self.cargar_colores_asignados()

    def inicializar_ui(self):
        self.setWindowTitle("Esperando jugadores")
        self.setFixedSize(QSize(500, 400))

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
            radio = GuiRadioButtonColor("            ", self, self._main_window, color)
            self.radio_por_colores[color.name()] = radio

            # Añadir el color y el botón al layout horizontal
            fila_layout.addWidget(color_label)
            fila_layout.addWidget(radio)

            # Añadir el layout horizontal al layout principal
            layout.addLayout(fila_layout)

        layout.addLayout(grid_layout)

        # Añadir botón de "Empezar" si es admin
        if self._main_window.client.es_admin():
            empezar_button = QPushButton("Empezar")
            empezar_button.setFixedSize(100, 50)
            empezar_button.clicked.connect(self.empezar_juego)

            # Crear un layout horizontal para centrar el botón
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(empezar_button)
            button_layout.addStretch()

            layout.addLayout(button_layout)

        self.setLayout(layout)

    def empezar_juego(self):
        self._main_window.transmisor.empezar_partida()

    def cargar_colores_asignados(self):
        print("cargar_colores_asignados")
        self.limpiar()
        colores_asignados = self._main_window.colores.colores_asignados()
        print(colores_asignados)
        for user_id, color in colores_asignados.items():
            print(f"{user_id=} {color=}")
            radio = self.radio_por_colores.get(color.name())
            print(f"{radio}=")
            if radio:
                client = self._main_window.client_by_id.get(user_id)
                if client:
                    print(f"{client.username()=}")
                    radio.seleccionar(f"{client.username()}")

    def limpiar(self):
        for radio in self.radio_por_colores.values():
            radio.limpiar()
