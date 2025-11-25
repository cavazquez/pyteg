from __future__ import annotations

import contextlib
from typing import Any

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
from src.i18n import translate as _


class VentanaConectar(QDialog):
    def __init__(self, main_window: Any):
        super().__init__(parent=main_window)
        self._main_window = main_window
        self.addr: QLineEdit
        self.port: QLineEdit
        self.username: QLineEdit
        self._conexion: ConnectionClient | None = None

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

        # Conectar al selector de idioma para cambios dinámicos
        self._connect_to_language_selector()

    def _setup_window(self) -> None:
        """Configura las propiedades básicas de la ventana"""
        self.setWindowTitle(_("Conectar al servidor"))
        self.setFixedSize(QSize(400, 300))
        # Quitar botones de maximizar, minimizar y ayuda, dejando solo el de cerrar
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Configura el título y la descripción"""
        # Título
        title_label = QLabel(_("Conectar a Partida"))
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212529;
            margin-bottom: 5px;
        """)
        parent_layout.addWidget(title_label)

        # Descripción
        desc_label = QLabel(
            _("Ingresa los datos para conectarte a una partida existente")
        )
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 10px;
        """)
        parent_layout.addWidget(desc_label)

    def _setup_form(self, parent_layout: QVBoxLayout) -> None:
        """Configura el formulario con los campos de entrada"""
        # Crear layout de formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        # Crear campos de entrada
        self._create_input_fields()

        # Crear etiquetas con estilo
        label_style = "font-weight: bold; color: #495057; font-size: 13px;"

        addr_label = QLabel(_("Dirección:"))
        addr_label.setStyleSheet(label_style)

        port_label = QLabel(_("Puerto:"))
        port_label.setStyleSheet(label_style)

        user_label = QLabel(_("Usuario:"))
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

    def _create_input_fields(self) -> None:
        """Crea y estiliza los campos de entrada"""
        # Campos de entrada
        self.addr = QLineEdit("localhost")
        self.addr.setPlaceholderText(_("Dirección del servidor"))

        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator())
        self.port.setPlaceholderText(_("Puerto"))

        self.username = QLineEdit()
        self.username.setPlaceholderText(_("Tu nombre en el juego"))

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

    def _setup_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Configura los botones de acción"""
        # Añadir espacio vertical antes de los botones
        spacer = QLabel()
        spacer.setFixedHeight(15)
        parent_layout.addWidget(spacer)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botón cancelar
        button_cancelar = QPushButton(_("Cancelar"))
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
        button_conectar = QPushButton(_("Conectar"))
        button_conectar.setDefault(True)
        button_conectar.clicked.connect(self.connect_to_server)
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

    def _apply_general_style(self) -> None:
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

    def connect_to_server(self) -> None:
        """Intenta conectarse al servidor con los datos proporcionados"""
        try:
            addr = self.addr.text()
            port = int(self.port.text())
            username = self.username.text().strip()

            # Validar campos
            if not addr:
                self._show_error(
                    _("Por favor ingresa una dirección de servidor válida")
                )
                self.addr.setFocus()
                return

            if not port:
                self._show_error(_("Por favor ingresa un puerto válido"))
                self.port.setFocus()
                return

            if not username:
                self._show_error(_("Por favor ingresa un nombre de usuario"))
                self.username.setFocus()
                return

            # Intentar conexión
            self._conexion = ConnectionClient(self._main_window, addr, port, username)
            self._conexion.conectar()

            # Configurar el transmisor en main_window
            self._main_window.transmisor = ClientTransmisor(self._conexion)
            self.accept()  # Cerrar el diálogo si la conexión es exitosa

        except (ConnectionError, OSError, ValueError) as e:
            self._show_error(_("Error al conectar: {}").format(str(e)))

    def _show_error(self, message: str) -> None:
        """Muestra un mensaje de error con estilo mejorado"""
        error_box = QMessageBox(self)
        error_box.setWindowTitle(_("Error de conexión"))
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setStandardButtons(QMessageBox.StandardButton.Ok)

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
        error_box.exec()

    def _connect_to_language_selector(self) -> None:
        """Conecta al selector de idioma para cambios dinámicos"""
        try:
            # Conectar directamente al selector de idioma de la ventana principal
            if hasattr(self._main_window, "language_selector") and hasattr(
                self._main_window.language_selector, "language_changed"
            ):
                # Desconectar cualquier conexión anterior para evitar duplicados
                with contextlib.suppress(TypeError, RuntimeError):
                    self._main_window.language_selector.language_changed.disconnect(
                        self.update_language
                    )

                # Conectar la señal
                self._main_window.language_selector.language_changed.connect(
                    self.update_language
                )

        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"DEBUG: Error conectando al selector de idioma: {e}")

    def update_language(self) -> None:
        """Actualiza todos los textos de la interfaz al cambiar el idioma"""

        # Actualizar título de la ventana
        self.setWindowTitle(_("Conectar al servidor"))

        # Buscar y actualizar todos los QLabel
        labels = self.findChildren(QLabel)
        for label in labels:
            current_text = label.text()
            if current_text in {"Conectar a Partida", "Connect to Game"}:
                label.setText(_("Conectar a Partida"))
            elif current_text in {
                "Ingresa los datos para conectarte a una partida existente",
                "Enter the details to connect to an existing game",
            }:
                label.setText(
                    _("Ingresa los datos para conectarte a una partida existente")
                )
            elif current_text in {"Dirección:", "Address:", "Direccion:"}:
                label.setText(_("Dirección:"))
            elif current_text in {"Puerto:", "Port:"}:
                label.setText(_("Puerto:"))
            elif current_text in {"Usuario:", "User:"}:
                label.setText(_("Usuario:"))

        # Buscar y actualizar todos los QPushButton
        buttons = self.findChildren(QPushButton)
        for button in buttons:
            current_text = button.text()
            if current_text in {"Cancelar", "Cancel"}:
                button.setText(_("Cancelar"))
            elif current_text in {"Conectar", "Connect"}:
                button.setText(_("Conectar"))

        # Actualizar placeholders
        if hasattr(self, "addr"):
            self.addr.setPlaceholderText(_("Dirección del servidor"))
        if hasattr(self, "port"):
            self.port.setPlaceholderText(_("Puerto"))
        if hasattr(self, "username"):
            self.username.setPlaceholderText(_("Tu nombre en el juego"))
