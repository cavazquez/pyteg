from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.client_connection import ConnectionClient
from src.client_transmisor import ClientTransmisor


class VentanaConectar(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

        # Configurar ventana
        self._setup_window()

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Añadir componentes al layout principal
        self._setup_header(main_layout)
        self._setup_form(main_layout)
        self._setup_buttons(main_layout)

        # Aplicar estilo general al diálogo
        self._apply_general_style()

        # Establecer el layout principal
        self.setLayout(main_layout)

    def _setup_window(self):
        """Configura las propiedades básicas de la ventana"""
        self.setWindowTitle("Conectar al servidor")
        self.setFixedSize(QSize(400, 300))
        # Quitar botones de maximizar, minimizar y ayuda, dejando solo el de cerrar
        self.setWindowFlags(
            Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )

    def _setup_header(self, parent_layout):
        """Configura el título y la descripción"""
        # Título
        title_label = QLabel("Conectar a Partida")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212529;
            margin-bottom: 5px;
        """)
        parent_layout.addWidget(title_label)

        # Descripción
        desc_label = QLabel("Ingresa los datos para conectarte a una partida existente")
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 10px;
        """)
        parent_layout.addWidget(desc_label)

    def _setup_form(self, parent_layout):
        """Configura el formulario con los campos de entrada"""
        # Crear layout de formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignLeft)

        # Crear campos de entrada
        self._create_input_fields()

        # Crear etiquetas con estilo
        label_style = "font-weight: bold; color: #495057; font-size: 13px;"

        addr_label = QLabel("Dirección:")
        addr_label.setStyleSheet(label_style)

        port_label = QLabel("Puerto:")
        port_label.setStyleSheet(label_style)

        user_label = QLabel("Usuario:")
        user_label.setStyleSheet(label_style)

        # Añadir campos al formulario con espaciadores entre ellos
        form_layout.addRow(addr_label, self.addr)

        # Espaciador entre campos
        spacer1 = QLabel()
        spacer1.setFixedHeight(10)
        form_layout.addRow("", spacer1)

        form_layout.addRow(port_label, self.port)

        # Espaciador entre campos
        spacer2 = QLabel()
        spacer2.setFixedHeight(10)
        form_layout.addRow("", spacer2)

        form_layout.addRow(user_label, self.username)

        parent_layout.addLayout(form_layout)

    def _create_input_fields(self):
        """Crea y estiliza los campos de entrada"""
        # Campos de entrada
        self.addr = QLineEdit("localhost")
        self.addr.setPlaceholderText("Dirección del servidor")

        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator())
        self.port.setPlaceholderText("Puerto")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Tu nombre en el juego")

        # Estilo para los campos
        input_style = """
            QLineEdit {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
                min-height: 16px;
                height: 24px;
            }
            QLineEdit:focus {
                border-color: #4361ee;
                outline: none;
            }
        """
        self.addr.setStyleSheet(input_style)
        self.port.setStyleSheet(input_style)
        self.username.setStyleSheet(input_style)

    def _setup_buttons(self, parent_layout):
        """Configura los botones de acción"""
        # Añadir espacio vertical antes de los botones
        spacer = QLabel()
        spacer.setFixedHeight(15)
        parent_layout.addWidget(spacer)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botón cancelar
        button_cancelar = QPushButton("Cancelar")
        button_cancelar.clicked.connect(self.reject)
        button_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: #6c757d;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)

        # Botón conectar
        button_conectar = QPushButton("Conectar")
        button_conectar.setDefault(True)
        button_conectar.clicked.connect(self.connect)
        button_conectar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                background-color: #4361ee;
                color: white;
                font-weight: bold;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2f46c2;
            }
        """)

        # Añadir botones al layout
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(button_cancelar)
        buttons_layout.addWidget(button_conectar)

        parent_layout.addLayout(buttons_layout)

    def _apply_general_style(self):
        """Aplica estilos generales al diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFormLayout {
                margin-top: 5px;
                margin-bottom: 5px;
            }
        """)

    def connect(self):
        """Intenta conectarse al servidor con los datos proporcionados"""
        try:
            addr = self.addr.text()
            port = int(self.port.text())
            username = self.username.text().strip()

            # Validar campos
            if not addr:
                self._show_error("Por favor ingresa una dirección de servidor válida")
                self.addr.setFocus()
                return

            if not port:
                self._show_error("Por favor ingresa un puerto válido")
                self.port.setFocus()
                return

            if not username:
                self._show_error("Por favor ingresa un nombre de usuario")
                self.username.setFocus()
                return

            # Intentar conexión
            self._conexion = ConnectionClient(self._main_window, addr, port, username)
            self._conexion.conectar()

            # Configurar el transmisor en main_window
            self._main_window.transmisor = ClientTransmisor(self._conexion)
            self.accept()  # Cerrar el diálogo si la conexión es exitosa

        except Exception as e:
            self._show_error(f"Error al conectar: {e!s}")

    def _show_error(self, message):
        """Muestra un mensaje de error con estilo mejorado"""
        error_box = QMessageBox(self)
        error_box.setWindowTitle("Error de conexión")
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setStandardButtons(QMessageBox.Ok)

        # Estilo para el mensaje de error
        error_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #212529;
                font-size: 13px;
                min-width: 300px;
            }
            QPushButton {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                background-color: #4361ee;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
        """)

        error_box.exec_()
