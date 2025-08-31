from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.i18n import translate as _


class TarjetaWidget(QWidget):
    """Widget que representa una tarjeta individual."""

    def __init__(self, pais, simbolo):
        super().__init__()
        self.pais = pais
        self.simbolo = simbolo
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

        self.setFixedSize(120, 80)


class TarjetasDialog(QDialog):
    """Diálogo para mostrar las tarjetas asignadas al jugador."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Mis Tarjetas"))
        self.setModal(True)
        self.setFixedSize(600, 400)

        # Lista de tarjetas de ejemplo (máximo 4)
        self.tarjetas = [
            {"pais": "Circulo", "simbolo": "Galeon"},
            {"pais": "Rectangulo", "simbolo": "Globo"},
            # Agregar más tarjetas de prueba si es necesario
        ]

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

        # Mostrar tarjetas en una grilla de 2x2 (máximo 4 tarjetas)
        for i, tarjeta in enumerate(self.tarjetas[:4]):  # Máximo 4 tarjetas
            tarjeta_widget = TarjetaWidget(tarjeta["pais"], tarjeta["simbolo"])
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
        # Lógica pendiente de implementar
        # self.button_canje.clicked.connect(self.realizar_canje)

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
