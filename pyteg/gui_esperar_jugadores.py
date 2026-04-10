"""Módulo para la ventana de espera de jugadores."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui_radio_color import GuiRadioButtonColor


class VentanaEsperarJugadores(QWidget):
    """Ventana para esperar a que los jugadores se conecten y seleccionen colores."""

    def __init__(self, main_window: Any) -> None:
        """Inicializa la ventana de espera de jugadores.

        Args:
            main_window: Ventana principal de la aplicación.

        """
        super().__init__()
        self._main_window = main_window
        self._main_layout: QVBoxLayout | None = None
        self.radio_por_colores: dict[str, GuiRadioButtonColor] = {}
        self._initialized = False
        self.inicializar_ui()
        self._initialized = True
        self.cargar_colores_asignados()

        # Configurar para que se elimine al cerrar
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def inicializar_ui(self) -> None:
        """Inicializa la interfaz de usuario de la ventana."""
        self.setWindowTitle("Esperando jugadores")
        self.setFixedSize(QSize(500, 400))

        # Crear el layout principal
        self._main_layout = QVBoxLayout()
        self.setLayout(self._main_layout)

        # Crear un widget contenedor para los colores
        self.colores_widget = QWidget()
        self.colores_layout = QVBoxLayout()
        self.colores_widget.setLayout(self.colores_layout)

        # Añadir el widget de colores al layout principal
        self._main_layout.addWidget(self.colores_widget)

        # Crear botones de radio para cada color
        self.actualizar_botones_colores()

        # Añadir botón de "Empezar" si es admin
        client = getattr(self._main_window, "client", None)
        if client is not None and hasattr(client, "es_admin") and client.es_admin():
            empezar_button = QPushButton("Empezar")
            empezar_button.setFixedSize(100, 50)
            empezar_button.clicked.connect(self.empezar_juego)

            # Crear un layout horizontal para centrar el botón
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(empezar_button)
            button_layout.addStretch()

            self._main_layout.addLayout(button_layout)

    def empezar_juego(self) -> None:
        """Inicia el juego enviando el mensaje al servidor."""
        transmisor = getattr(self._main_window, "transmisor", None)
        if transmisor is not None:
            transmisor.empezar_partida()

    def cargar_colores_asignados(self) -> None:
        """Carga y muestra los colores asignados a los jugadores."""
        if not self._initialized:
            return

        print("=== Cargando colores asignados ===")
        self.limpiar()
        colores_manager = getattr(self._main_window, "colores", None)
        if colores_manager is None:
            return
        colores_asignados = colores_manager.colores_asignados()
        print(f"Colores asignados: {colores_asignados}")

        for user_id, color in colores_asignados.items():
            print(f"{user_id=} {color=}")
            radio = self.radio_por_colores.get(color.name())
            print(f"{radio=}")
            if radio:
                client = self._main_window.client_by_id.get(user_id)
                if client is None:
                    print(f"  - No se encontró cliente para el ID {user_id}")
                    continue

            if client and radio:
                print(
                    f"  - Asignando usuario {client.username()} al color {color.name()}"
                )
                radio.seleccionar(f"{client.username()}")

    def actualizar_botones_colores(self) -> None:
        """Actualiza los botones de radio para cada color disponible."""
        print("=== Actualizando botones de colores ===")

        # Verificar si ya hay widgets en el layout
        if self.colores_layout.count() > 0:
            print(f"  - Limpiando {self.colores_layout.count()} widgets existentes")
            # Crear una lista temporal de los widgets a eliminar
            widgets_para_eliminar = []
            for i in range(self.colores_layout.count()):
                item = self.colores_layout.itemAt(i)
                if item.widget():
                    widgets_para_eliminar.append(item.widget())
                elif item.layout():
                    for j in range(item.layout().count()):
                        subitem = item.layout().itemAt(j)
                        if subitem and subitem.widget():
                            widgets_para_eliminar.append(subitem.widget())

            # Eliminar los widgets
            for widget in widgets_para_eliminar:
                widget.setParent(None)
                widget.deleteLater()

        # Limpiar el diccionario de radios
        self.radio_por_colores.clear()

        # Obtener colores únicos
        colores_manager = getattr(self._main_window, "colores", None)
        if colores_manager is None:
            return
        colores = list(
            {color.name(): color for color in colores_manager.colores()}.values()
        )
        print(f"  - Creando {len(colores)} botones de colores")

        # Crear nuevos botones de radio para cada color
        for color in colores:
            color_name = color.name()
            print(f"  - Creando botón para color {color_name}")

            # Crear un layout horizontal para cada fila
            fila_layout = QHBoxLayout()
            fila_layout.setSpacing(10)

            # Crear un widget para mostrar el color
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(
                f"background-color: {color_name}; "
                "border: 1px solid black; "
                "border-radius: 3px;"
            )

            # Crear el botón de radio con un ID único basado en el color
            radio = GuiRadioButtonColor("            ", self, self._main_window, color)
            radio.setObjectName(f"radio_{color_name}")
            self.radio_por_colores[color_name] = radio

            # Añadir el color y el botón al layout horizontal
            fila_layout.addWidget(color_label)
            fila_layout.addWidget(radio)
            fila_layout.addStretch()

            # Añadir la fila al layout de colores
            self.colores_layout.addLayout(fila_layout)

        print(f"  - Total de botones creados: {len(self.radio_por_colores)}")

    def limpiar(self) -> None:
        """Limpia todos los botones de radio de colores."""
        for radio in self.radio_por_colores.values():
            radio.limpiar()
