"""Diálogo Qt para conectarse al servidor."""

from __future__ import annotations

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

from pyteg.client.conexion.connection import ConnectionClient
from pyteg.client.conexion.transmisor import ClientTransmisor
from pyteg.gui.dialogs.conectar import styles
from pyteg.gui.dialogs.conectar.validation import ValidationError, validate
from pyteg.i18n import translate as _
from pyteg.logger import get_logger

_LOG = get_logger("gui.conectar")


class VentanaConectar(QDialog):
    """Ventana de diálogo para conectarse al servidor."""

    def __init__(self, main_window: Any) -> None:
        """Inicializa la ventana de conexión.

        Args:
            main_window: Ventana principal de la aplicación.

        """
        super().__init__(parent=main_window)
        self._main_window = main_window
        self.addr: QLineEdit
        self.port: QLineEdit
        self.username: QLineEdit
        self._conexion: ConnectionClient | None = None

        self._setup_window()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self._setup_header(main_layout)
        self._setup_form(main_layout)
        self._setup_buttons(main_layout)

        self._apply_general_style()

        self.setLayout(main_layout)

        self._connect_to_language_selector()

    def _setup_window(self) -> None:
        """Configura las propiedades básicas de la ventana."""
        self.setWindowTitle(_("Conectar al servidor"))
        self.setFixedSize(QSize(400, 300))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Configura el título y la descripción."""
        title_label = QLabel(_("Conectar a Partida"))
        title_label.setStyleSheet(styles.TITLE_LABEL_STYLE)
        parent_layout.addWidget(title_label)

        desc_label = QLabel(
            _("Ingresa los datos para conectarte a una partida existente")
        )
        desc_label.setStyleSheet(styles.DESC_LABEL_STYLE)
        parent_layout.addWidget(desc_label)

    def _setup_form(self, parent_layout: QVBoxLayout) -> None:
        """Configura el formulario con los campos de entrada."""
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self._create_input_fields()

        addr_label = QLabel(_("Dirección:"))
        addr_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        port_label = QLabel(_("Puerto:"))
        port_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        user_label = QLabel(_("Usuario:"))
        user_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        form_layout.addRow(addr_label, self.addr)

        spacer1 = QLabel()
        spacer1.setFixedHeight(10)
        form_layout.addRow("", spacer1)

        form_layout.addRow(port_label, self.port)

        spacer2 = QLabel()
        spacer2.setFixedHeight(10)
        form_layout.addRow("", spacer2)

        form_layout.addRow(user_label, self.username)

        parent_layout.addLayout(form_layout)

    def _create_input_fields(self) -> None:
        """Crea y estiliza los campos de entrada."""
        self.addr = QLineEdit("localhost")
        self.addr.setPlaceholderText(_("Dirección del servidor"))

        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator())
        self.port.setPlaceholderText(_("Puerto"))

        self.username = QLineEdit()
        self.username.setPlaceholderText(_("Tu nombre en el juego"))

        self.addr.setStyleSheet(styles.INPUT_STYLE)
        self.port.setStyleSheet(styles.INPUT_STYLE)
        self.username.setStyleSheet(styles.INPUT_STYLE)

    def _setup_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Configura los botones de acción."""
        spacer = QLabel()
        spacer.setFixedHeight(15)
        parent_layout.addWidget(spacer)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        button_cancelar = QPushButton(_("Cancelar"))
        button_cancelar.clicked.connect(self.reject)
        button_cancelar.setStyleSheet(styles.CANCEL_BUTTON_STYLE)

        button_conectar = QPushButton(_("Conectar"))
        button_conectar.setDefault(True)
        button_conectar.clicked.connect(self.connect_to_server)
        button_conectar.setStyleSheet(styles.CONNECT_BUTTON_STYLE)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(button_cancelar)
        buttons_layout.addWidget(button_conectar)

        parent_layout.addLayout(buttons_layout)

    def _apply_general_style(self) -> None:
        """Aplica estilos generales al diálogo."""
        self.setStyleSheet(styles.DIALOG_STYLE)

    def connect_to_server(self) -> None:
        """Intenta conectarse al servidor con los datos proporcionados."""
        result = validate(self.addr.text(), self.port.text(), self.username.text())
        if isinstance(result, ValidationError):
            self._show_error(result.message)
            if result.field == "addr":
                self.addr.setFocus()
            elif result.field == "port":
                self.port.setFocus()
            elif result.field == "username":
                self.username.setFocus()
            return

        addr, port, username = result
        try:
            self._conexion = ConnectionClient(self._main_window, addr, port, username)
            self._conexion.conectar()

            self._main_window.transmisor = ClientTransmisor(self._conexion)
            self.accept()

        except (ConnectionError, OSError, ValueError) as e:
            self._show_error(_("Error al conectar: {}").format(str(e)))

    def _show_error(self, message: str) -> None:
        """Muestra un mensaje de error con estilo mejorado."""
        error_box = QMessageBox(self)
        error_box.setWindowTitle(_("Error de conexión"))
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        error_box.setStyleSheet(styles.ERROR_BOX_STYLE)
        error_box.exec()

    def _connect_to_language_selector(self) -> None:
        """Conecta al selector de idioma para cambios dinámicos."""
        try:
            if hasattr(self._main_window, "language_selector") and hasattr(
                self._main_window.language_selector, "language_changed"
            ):
                # UniqueConnection: evita duplicar el slot si este método se llama
                # más de una vez; no usar disconnect() antes del primer connect (Qt
                # emite RuntimeWarning si no había enlace).
                self._main_window.language_selector.language_changed.connect(
                    self.update_language,
                    Qt.ConnectionType.UniqueConnection,
                )

        except (AttributeError, TypeError, RuntimeError) as e:
            _LOG.debug("Error conectando al selector de idioma: %s", e)

    def update_language(self) -> None:
        """Actualiza todos los textos de la interfaz al cambiar el idioma."""
        self.setWindowTitle(_("Conectar al servidor"))

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

        buttons = self.findChildren(QPushButton)
        for button in buttons:
            current_text = button.text()
            if current_text in {"Cancelar", "Cancel"}:
                button.setText(_("Cancelar"))
            elif current_text in {"Conectar", "Connect"}:
                button.setText(_("Conectar"))

        if hasattr(self, "addr"):
            self.addr.setPlaceholderText(_("Dirección del servidor"))
        if hasattr(self, "port"):
            self.port.setPlaceholderText(_("Puerto"))
        if hasattr(self, "username"):
            self.username.setPlaceholderText(_("Tu nombre en el juego"))
