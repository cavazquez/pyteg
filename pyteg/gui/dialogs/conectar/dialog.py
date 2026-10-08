"""Diálogo Qt para conectarse al servidor."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
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
from pyteg.client.hosting import local_game_addresses
from pyteg.config import DEFAULT_MAP_THEME
from pyteg.exceptions import ImagenNoEncontradaError
from pyteg.gui.dialogs.conectar import styles
from pyteg.gui.dialogs.conectar.validation import (
    TCP_MAX_PORT,
    TCP_MIN_PORT,
    ValidationError,
    validate,
)
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.server.hosting.runtime import HostRuntime
from pyteg.toml_reader import TomlReaderError

_LOG = get_logger("gui.conectar")

# Variantes ES/EN del texto actual → msgid a re-traducir
_CONNECT_TEXT_TO_MSGID: dict[str, str] = {
    "Conectar a Partida": "Conectar a Partida",
    "Connect to Game": "Conectar a Partida",
    "Ingresa los datos para conectarte a una partida existente": (
        "Ingresa los datos para conectarte a una partida existente"
    ),
    "Enter the details to connect to an existing game": (
        "Ingresa los datos para conectarte a una partida existente"
    ),
    "Dirección:": "Dirección:",
    "Address:": "Dirección:",
    "Direccion:": "Dirección:",
    "Puerto:": "Puerto:",
    "Port:": "Puerto:",
    "Usuario:": "Usuario:",
    "User:": "Usuario:",
    "Mapa:": "Mapa:",
    "Map:": "Mapa:",
    "Cancelar": "Cancelar",
    "Cancel": "Cancelar",
    "Conectar": "Conectar",
    "Connect": "Conectar",
}


def _retranslate_widget_texts(
    widgets: list[QLabel | QPushButton], replacements: dict[str, str]
) -> None:
    for widget in widgets:
        msgid = replacements.get(widget.text())
        if msgid is not None:
            widget.setText(_(msgid))


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
        self.theme_selector: QComboBox
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
        self._update_mode()

        self._connect_to_language_selector()

    def _setup_window(self) -> None:
        """Configura las propiedades básicas de la ventana."""
        self.setWindowTitle(_("Crear o unirse a una partida"))
        self.setFixedSize(QSize(440, 440))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Configura el título y la descripción."""
        title_label = QLabel(_("Unirme a una partida"))
        self.title_label = title_label
        title_label.setStyleSheet(styles.TITLE_LABEL_STYLE)
        parent_layout.addWidget(title_label)

        desc_label = QLabel(
            _("Ingresa los datos para conectarte a una partida existente")
        )
        self.description_label = desc_label
        desc_label.setWordWrap(True)
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

        self.mode_selector = QComboBox()
        self.mode_selector.addItem(_("Unirme a una partida"), "join")
        self.mode_selector.addItem(_("Crear partida"), "host")
        self.mode_selector.setStyleSheet(styles.INPUT_STYLE)
        self.mode_selector.currentIndexChanged.connect(self._update_mode)
        self.mode_label = QLabel(_("Acción:"))
        self.mode_label.setStyleSheet(styles.FORM_LABEL_STYLE)
        form_layout.addRow(self.mode_label, self.mode_selector)

        addr_label = QLabel(_("Dirección:"))
        addr_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        port_label = QLabel(_("Puerto:"))
        port_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        user_label = QLabel(_("Usuario:"))
        user_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        self.theme_label = QLabel(_("Mapa:"))
        self.theme_label.setStyleSheet(styles.FORM_LABEL_STYLE)

        form_layout.addRow(addr_label, self.addr)

        form_layout.addRow(port_label, self.port)

        form_layout.addRow(user_label, self.username)
        form_layout.addRow(self.theme_label, self.theme_selector)

        parent_layout.addLayout(form_layout)
        self.host_hint = QLabel(
            _(
                "Los demás jugadores se conectan a tu dirección y puerto "
                "en la red local."
            )
        )
        self.host_hint.setWordWrap(True)
        self.host_hint.setStyleSheet(styles.DESC_LABEL_STYLE)
        parent_layout.addWidget(self.host_hint)

    def _update_mode(self) -> None:
        hosting = self.mode_selector.currentData() == "host"
        if hosting and not self.addr.isReadOnly():
            self._join_address = self.addr.text()
            self.addr.setText(", ".join(local_game_addresses()))
        elif not hosting and self.addr.isReadOnly():
            self.addr.setText(self._join_address)
        self.addr.setReadOnly(hosting)
        self.host_hint.setVisible(hosting)
        self.title_label.setText(
            _("Crear partida") if hosting else _("Unirme a una partida")
        )
        self.description_label.setText(
            _("Tu computadora alojará la partida mientras jugás.")
            if hosting
            else _("Ingresa los datos para conectarte a una partida existente")
        )
        self.connect_button.setText(_("Crear partida") if hosting else _("Conectar"))

    def _create_input_fields(self) -> None:
        """Crea y estiliza los campos de entrada."""
        self.addr = QLineEdit("localhost")
        self.addr.setPlaceholderText(_("Dirección del servidor"))

        self.port = QLineEdit("65432")
        self.port.setValidator(QIntValidator(TCP_MIN_PORT, TCP_MAX_PORT, self.port))
        self.port.setPlaceholderText(_("Puerto"))

        self.username = QLineEdit()
        self.username.setPlaceholderText(_("Tu nombre en el juego"))

        self.theme_selector = QComboBox()
        self.theme_selector.addItem(_("Clásico"), "classic")
        self.theme_selector.addItem(_("Revancha"), "revancha")
        selected_theme = getattr(self._main_window, "map_theme", DEFAULT_MAP_THEME)
        selected_index = self.theme_selector.findData(selected_theme)
        if selected_index >= 0:
            self.theme_selector.setCurrentIndex(selected_index)

        self.addr.setStyleSheet(styles.INPUT_STYLE)
        self.port.setStyleSheet(styles.INPUT_STYLE)
        self.username.setStyleSheet(styles.INPUT_STYLE)
        self.theme_selector.setStyleSheet(styles.INPUT_STYLE)

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

        button_conectar = QPushButton(_("Continuar"))
        self.connect_button = button_conectar
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
        conexion_actual = getattr(self._main_window, "conexion", None)
        if (
            isinstance(conexion_actual, ConnectionClient)
            and conexion_actual.esta_ocupada()
        ):
            self._show_error(
                _(
                    "Ya existe una conexión activa o en curso en esta ventana. "
                    "Desconéctala antes de conectar otra."
                )
            )
            return

        hosting = self.mode_selector.currentData() == "host"
        result = validate(
            "127.0.0.1" if hosting else self.addr.text(),
            self.port.text(),
            self.username.text(),
        )
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
        selected_theme = self.theme_selector.currentData()
        try:
            self._main_window.set_map_theme(selected_theme)
        except (OSError, ValueError, TomlReaderError, ImagenNoEncontradaError) as e:
            self._show_error(_("No se pudo cargar el mapa: {}").format(str(e)))
            return

        try:
            if isinstance(conexion_actual, ConnectionClient):
                conexion_actual.desconectar()
            if hosting:
                port = self._create_host(selected_theme, port)
            self._conexion = ConnectionClient(self._main_window, addr, port, username)
            self._main_window.conexion = self._conexion
            self._conexion.conectar()

            self._main_window.transmisor = ClientTransmisor(self._conexion)
            self.accept()

        except (ConnectionError, OSError, ValueError) as e:
            self._show_error(_("Error al conectar: {}").format(str(e)))

    def _create_host(self, theme: str, port: int) -> int:
        """Crea el anfitrión y conserva sus recursos sólo si pudo reservar el puerto.

        Returns:
            Puerto de la sala creada.

        Raises:
            OSError: Si no se puede escuchar en el puerto solicitado.
            ValueError: Si el mapa o la sala no son válidos.

        """
        previous = getattr(self._main_window, "host_runtime", None)
        if isinstance(previous, HostRuntime):
            previous.close()
        runtime = HostRuntime()
        try:
            port = runtime.create_game(theme, port)
        except OSError, ValueError:
            runtime.close()
            raise
        self._main_window.host_runtime = runtime
        self._main_window.reset_session_state()
        return port

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
        self.setWindowTitle(_("Crear o unirse a una partida"))
        _retranslate_widget_texts(self.findChildren(QLabel), _CONNECT_TEXT_TO_MSGID)
        _retranslate_widget_texts(
            self.findChildren(QPushButton), _CONNECT_TEXT_TO_MSGID
        )

        if hasattr(self, "addr"):
            self.addr.setPlaceholderText(_("Dirección del servidor"))
        if hasattr(self, "port"):
            self.port.setPlaceholderText(_("Puerto"))
        if hasattr(self, "username"):
            self.username.setPlaceholderText(_("Tu nombre en el juego"))
        self.theme_label.setText(_("Mapa:"))
        self.theme_selector.setItemText(0, _("Clásico"))
        self.theme_selector.setItemText(1, _("Revancha"))
        self.mode_selector.setItemText(0, _("Unirme a una partida"))
        self.mode_selector.setItemText(1, _("Crear partida"))
        self.mode_label.setText(_("Acción:"))
        self.host_hint.setText(
            _(
                "Los demás jugadores se conectan a tu dirección y puerto "
                "en la red local."
            )
        )
        self._update_mode()
