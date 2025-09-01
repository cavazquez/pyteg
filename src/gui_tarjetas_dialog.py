from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.i18n import translate as _


class TarjetaWidget(QWidget):
    """Widget que representa una tarjeta individual."""

    seleccionada = Signal(object)  # Señal emitida cuando se selecciona/deselecciona

    def __init__(self, pais, simbolo, index=0):
        super().__init__()
        self.pais = pais
        self.simbolo = simbolo
        self.index = index
        self._seleccionada = False
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz del widget de tarjeta."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Etiqueta del país
        self.label_pais = QLabel(self.pais)
        self.label_pais.setAlignment(Qt.AlignCenter)
        self.label_pais.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

        # Etiqueta del símbolo
        self.label_simbolo = QLabel(self.simbolo)
        self.label_simbolo.setAlignment(Qt.AlignCenter)
        self.label_simbolo.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                margin-top: 5px;
            }
        """)

        layout.addWidget(self.label_pais)
        layout.addWidget(self.label_simbolo)
        self.setLayout(layout)

        # Estilo del widget completo
        self._actualizar_estilo()
        self.setFixedSize(120, 80)

        # Hacer el widget clickeable
        self.setCursor(Qt.PointingHandCursor)

    def _actualizar_estilo(self):
        """Actualiza el estilo según el estado de selección."""
        if self._seleccionada:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: #e8f5e8;
                    border: 3px solid #27ae60;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #229954;
                    background-color: #d5f4d5;
                }
            """)
        else:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: white;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #2980b9;
                    background-color: #ecf0f1;
                }
            """)

    def mousePressEvent(self, event):  # noqa: N802
        """Maneja el clic en la tarjeta para seleccionar/deseleccionar."""
        if event.button() == Qt.LeftButton:
            self.toggle_seleccion()
        super().mousePressEvent(event)

    def toggle_seleccion(self):
        """Alterna el estado de selección de la tarjeta."""
        self._seleccionada = not self._seleccionada
        self._actualizar_estilo()
        self.seleccionada.emit(self)

    def set_seleccionada(self, seleccionada):
        """Establece el estado de selección de la tarjeta."""
        if self._seleccionada != seleccionada:
            self._seleccionada = seleccionada
            self._actualizar_estilo()

    def is_seleccionada(self):
        """Retorna True si la tarjeta está seleccionada."""
        return self._seleccionada


class TarjetasDialog(QDialog):
    """Diálogo para mostrar las tarjetas asignadas al jugador."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Mis Tarjetas"))
        self.setModal(True)
        self.setFixedSize(600, 450)  # Aumentado para acomodar info de selección

        # Lista de tarjetas de ejemplo (máximo 4)
        self.tarjetas = [
            {"pais": "Circulo", "simbolo": "Galeon"},
            {"pais": "Rectangulo", "simbolo": "Globo"},
            # Agregar más tarjetas de prueba si es necesario
        ]

        # Lista de widgets de tarjetas para manejar selección
        self.tarjetas_widgets = []
        self.tarjetas_seleccionadas = []

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel(_("Tarjetas Asignadas"))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(titulo)

        # Área de tarjetas
        self.tarjetas_widget = self._create_tarjetas_area()
        layout.addWidget(self.tarjetas_widget)

        # Información de selección
        self.info_seleccion = self._create_info_seleccion()
        layout.addWidget(self.info_seleccion)

        # Botones de acción
        botones_layout = self._create_buttons_layout()
        layout.addLayout(botones_layout)

        # Botón cerrar
        cerrar_layout = QHBoxLayout()
        cerrar_layout.addStretch()

        self.button_cerrar = QPushButton(_("Cerrar"))
        self.button_cerrar.clicked.connect(self.accept)
        self.button_cerrar.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cerrar_layout.addWidget(self.button_cerrar)
        cerrar_layout.addStretch()

        layout.addLayout(cerrar_layout)
        self.setLayout(layout)

    def _create_tarjetas_area(self):
        """Crea el área donde se muestran las tarjetas."""
        widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignCenter)

        # Limpiar lista de widgets
        self.tarjetas_widgets.clear()

        # Mostrar tarjetas en una grilla de 2x2 (máximo 4 tarjetas)
        for i, tarjeta in enumerate(self.tarjetas[:4]):  # Máximo 4 tarjetas
            tarjeta_widget = TarjetaWidget(tarjeta["pais"], tarjeta["simbolo"], i)
            tarjeta_widget.seleccionada.connect(self._on_tarjeta_seleccionada)
            self.tarjetas_widgets.append(tarjeta_widget)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(tarjeta_widget, row, col)

        # Si hay menos de 4 tarjetas, mostrar espacios vacíos
        for i in range(len(self.tarjetas), 4):
            placeholder = QLabel(_("Vacío"))
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 2px dashed #bdc3c7;
                    border-radius: 8px;
                    color: #7f8c8d;
                    font-style: italic;
                }
            """)
            placeholder.setFixedSize(120, 80)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(placeholder, row, col)

        widget.setLayout(grid_layout)
        return widget

    def _create_buttons_layout(self):
        """Crea el layout con los botones de acción."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Botón Seleccionar Todas
        self.button_seleccionar_todas = QPushButton(_("Seleccionar Todas"))
        self.button_seleccionar_todas.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.button_seleccionar_todas.clicked.connect(self.seleccionar_todas)

        # Botón Deseleccionar Todas
        self.button_deseleccionar_todas = QPushButton(_("Deseleccionar Todas"))
        self.button_deseleccionar_todas.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.button_deseleccionar_todas.clicked.connect(self.deseleccionar_todas)

        layout.addWidget(self.button_seleccionar_todas)
        layout.addWidget(self.button_deseleccionar_todas)

        # Botón Reclamar Tarjeta
        self.button_reclamar = QPushButton(_("Reclamar Tarjeta"))
        self.button_reclamar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.button_reclamar.clicked.connect(self.reclamar_tarjeta)

        # Botón Canje
        self.button_canje = QPushButton(_("Canje"))
        self.button_canje.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.button_canje.clicked.connect(self.realizar_canje)
        self.button_canje.setEnabled(False)  # Deshabilitado hasta seleccionar tarjetas

        layout.addWidget(self.button_reclamar)
        layout.addWidget(self.button_canje)
        layout.addStretch()

        return layout

    def actualizar_tarjetas(self, nuevas_tarjetas):
        """Actualiza las tarjetas mostradas en el diálogo.

        Args:
            nuevas_tarjetas: Lista de diccionarios con 'pais' y 'simbolo'
        """
        self.tarjetas = nuevas_tarjetas[:4]  # Máximo 4 tarjetas

        # Recrear el área de tarjetas
        self.tarjetas_widget.setParent(None)
        self.tarjetas_widget = self._create_tarjetas_area()

        # Actualizar el layout
        layout = self.layout()
        layout.insertWidget(1, self.tarjetas_widget)

    def _create_info_seleccion(self):
        """Crea el área de información sobre la selección actual."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label_info_seleccion = QLabel(_("Seleccionadas: 0"))
        self.label_info_seleccion.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                margin: 5px;
            }
        """)

        layout.addWidget(self.label_info_seleccion)
        widget.setLayout(layout)
        return widget

    def _on_tarjeta_seleccionada(self, _tarjeta_widget):
        """Maneja la selección/deselección de una tarjeta."""
        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def _actualizar_lista_seleccionadas(self):
        """Actualiza la lista de tarjetas seleccionadas."""
        self.tarjetas_seleccionadas = [
            widget for widget in self.tarjetas_widgets if widget.is_seleccionada()
        ]

    def _actualizar_info_seleccion(self):
        """Actualiza la información mostrada sobre la selección."""
        cantidad = len(self.tarjetas_seleccionadas)
        self.label_info_seleccion.setText(_("Seleccionadas: %s") % cantidad)

        # Cambiar color según cantidad seleccionada
        if cantidad == 0:
            color = "#95a5a6"  # Gris
        elif cantidad <= 2:
            color = "#f39c12"  # Naranja
        else:
            color = "#27ae60"  # Verde

        self.label_info_seleccion.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: white;
                padding: 8px;
                background-color: {color};
                border-radius: 4px;
                margin: 5px;
            }}
        """)

    def _actualizar_estado_botones(self):
        """Actualiza el estado habilitado/deshabilitado de los botones."""
        cantidad_seleccionadas = len(self.tarjetas_seleccionadas)

        # El botón de canje se habilita con 3 tarjetas o con combinaciones válidas
        self.button_canje.setEnabled(self._puede_realizar_canje())

        # Botones de selección masiva
        total_tarjetas = len(self.tarjetas_widgets)
        self.button_seleccionar_todas.setEnabled(
            cantidad_seleccionadas < total_tarjetas
        )
        self.button_deseleccionar_todas.setEnabled(cantidad_seleccionadas > 0)

    def _puede_realizar_canje(self):
        """Determina si se puede realizar un canje con las tarjetas seleccionadas."""
        cantidad = len(self.tarjetas_seleccionadas)

        # Reglas básicas de canje (pueden ajustarse según las reglas del juego)
        if cantidad == 3:
            # Verificar si son 3 iguales o 3 diferentes
            simbolos = [tarjeta.simbolo for tarjeta in self.tarjetas_seleccionadas]
            return len(set(simbolos)) == 1 or len(set(simbolos)) == 3

        return False

    def seleccionar_todas(self):
        """Selecciona todas las tarjetas disponibles."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(True)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def deseleccionar_todas(self):
        """Deselecciona todas las tarjetas."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(False)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def realizar_canje(self):
        """Realiza el canje de las tarjetas seleccionadas."""
        if not self._puede_realizar_canje():
            return

        # Obtener información de las tarjetas seleccionadas
        tarjetas_info = [
            {"pais": tarjeta.pais, "simbolo": tarjeta.simbolo, "index": tarjeta.index}
            for tarjeta in self.tarjetas_seleccionadas
        ]

        try:
            # Enviar comando de canje al servidor
            if hasattr(self.parent(), "transmisor"):
                # Aquí se implementaría el envío al servidor
                # self.parent().transmisor.canjear_tarjetas(tarjetas_info)
                print(f"Canjeando tarjetas: {tarjetas_info}")

                # Por ahora, mostrar mensaje de confirmación
                QMessageBox.information(
                    self,
                    _("Canje Realizado"),
                    _("Se han canjeado %s tarjetas.") % len(tarjetas_info),
                )

                # Deseleccionar todas las tarjetas después del canje
                self.deseleccionar_todas()
            else:
                print("Error: No se puede acceder al transmisor")
        except (AttributeError, RuntimeError) as e:
            print(f"Error al realizar canje: {e}")

    def reclamar_tarjeta(self):
        """Reclama una tarjeta del servidor."""
        try:
            # Obtener referencia al transmisor desde la ventana padre
            if hasattr(self.parent(), "transmisor"):
                self.parent().transmisor.reclamar_tarjeta()
                # Solicitar tarjetas actualizadas inmediatamente después de reclamar
                self.parent().transmisor.solicitar_tarjetas()
            else:
                print("Error: No se puede acceder al transmisor")
        except (AttributeError, RuntimeError) as e:
            print(f"Error al reclamar tarjeta: {e}")
