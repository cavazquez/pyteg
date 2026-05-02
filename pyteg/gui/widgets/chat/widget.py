"""Widget Qt para el chat del juego (UI + integración con la ventana)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui.widgets.chat import format as fmt
from pyteg.gui.widgets.chat.styles import CHAT_STYLESHEET


class Chat(QWidget):
    """Widget de chat para comunicación entre jugadores."""

    def __init__(self, main_window: Any) -> None:
        """Inicializa el widget de chat.

        Args:
            main_window: Ventana principal de la aplicación.

        """
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario del chat."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.text_field.setMinimumHeight(150)
        self.text_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_field.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.text_field.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_field.setAcceptRichText(True)

        input_container = QWidget()
        input_container.setFixedHeight(40)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 2, 0, 2)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe un mensaje...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setMinimumHeight(30)

        self.send_button = QPushButton()
        self.send_button.setFixedSize(35, 30)
        self.send_button.setToolTip("Enviar mensaje")
        self.send_button.setText("➤")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field, 85)
        input_layout.addWidget(self.send_button, 15)

        main_layout.addWidget(self.text_field)
        main_layout.addWidget(input_container)

        self.setLayout(main_layout)

    def setup_styles(self) -> None:
        """Aplica la hoja de estilos del chat."""
        self.setStyleSheet(CHAT_STYLESHEET)

    def send_message(self) -> None:
        """Envía el mensaje escrito en el campo de entrada."""
        text = self.input_field.text().strip()
        if text:
            self.main_window.transmisor.enviar_chat(text)
            self.input_field.clear()
            self.input_field.setFocus()

    def append(self, text: str, msg_type: str = "normal") -> None:
        """Agrega un mensaje al área de chat.

        Args:
            text: Texto del mensaje.
            msg_type: Tipo de mensaje ("normal", "error", "system").

        """
        if msg_type == "error":
            formatted_text = fmt.format_error_message(text)
        elif msg_type == "system":
            formatted_text = fmt.format_system_message(text)
        elif text.startswith("Tú:"):
            formatted_text = fmt.format_self_message(text)
        else:
            formatted_text = self._format_user_message(text)

        self.text_field.append(formatted_text)
        self.text_field.verticalScrollBar().setValue(
            self.text_field.verticalScrollBar().maximum()
        )

    def _format_user_message(self, text: str) -> str:
        """Formatea un mensaje de otro usuario aplicando el color del jugador.

        Returns:
            Mensaje formateado en HTML.

        """
        return fmt.format_other_message(self.main_window.colores, text)

    def _get_user_color(self, username: str) -> str | None:
        """Obtiene el color hexadecimal del usuario.

        Returns:
            Color hexadecimal del usuario o None si no se encuentra.

        """
        return fmt.get_user_color(self.main_window.colores, username)
