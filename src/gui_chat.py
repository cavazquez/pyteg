"""Módulo para el widget de chat del juego."""

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
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Área de mensajes con scroll
        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.text_field.setMinimumHeight(150)
        self.text_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_field.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.text_field.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_field.setAcceptRichText(True)

        # Contenedor para el input y el botón
        input_container = QWidget()
        input_container.setFixedHeight(40)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 2, 0, 2)
        input_layout.setSpacing(8)

        # Campo de entrada de texto
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe un mensaje...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setMinimumHeight(30)

        # Botón de enviar
        self.send_button = QPushButton()
        self.send_button.setFixedSize(35, 30)
        self.send_button.setToolTip("Enviar mensaje")
        self.send_button.setText("➤")
        self.send_button.clicked.connect(self.send_message)

        # Agregar widgets al layout de entrada
        input_layout.addWidget(self.input_field, 85)
        input_layout.addWidget(self.send_button, 15)

        # Agregar widgets al layout principal
        main_layout.addWidget(self.text_field)
        main_layout.addWidget(input_container)

        # Establecer el layout principal
        self.setLayout(main_layout)

    def setup_styles(self) -> None:
        """Configura los estilos CSS del widget de chat."""
        # Estilos generales para la ventana
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #212529;
            }

            /* Estilo del título */
            QLabel {
                color: #343a40;
                padding: 5px;
            }

            /* Estilo del área de mensajes */
            QTextEdit {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: #212529;
                selection-background-color: #6c757d;
                selection-color: white;
            }

            QTextEdit QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }

            QTextEdit QScrollBar::handle:vertical {
                background: #adb5bd;
                min-height: 30px;
                border-radius: 4px;
            }

            QTextEdit QScrollBar::handle:vertical:hover {
                background: #6c757d;
            }

            QTextEdit QScrollBar::add-line:vertical,
            QTextEdit QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* Estilo del campo de entrada */
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 13px;
                background-color: white;
                color: #212529;
                min-height: 35px;
            }

            QLineEdit:focus {
                border-color: #4361ee;
                outline: 0;
            }

            QLineEdit::placeholder {
                color: #adb5bd;
                font-style: italic;
            }

            /* Estilo del botón de enviar */
            QPushButton {
                background-color: #4361ee;
                border: none;
                border-radius: 18px;
                color: white;
                font-weight: bold;
                font-size: 16px;
                min-width: 35px;
                min-height: 35px;
                padding: 0;
                text-align: center;
            }

            QPushButton:hover {
                background-color: #3a56d4;
            }

            QPushButton:pressed {
                background-color: #2f46c2;
            }

            QPushButton:disabled {
                background-color: #ced4da;
                color: #f8f9fa;
            }
        """)

    def send_message(self) -> None:
        """Envía el mensaje escrito en el campo de entrada."""
        text = self.input_field.text().strip()
        if text:
            # Enviar el mensaje
            self.main_window.transmisor.enviar_chat(text)

            # Limpiar el campo de entrada
            self.input_field.clear()

            # Dar foco nuevamente al campo de entrada para seguir escribiendo
            self.input_field.setFocus()

    def append(self, text: str, msg_type: str = "normal") -> None:
        """Agrega un mensaje al área de chat.

        Args:
            text: Texto del mensaje.
            msg_type: Tipo de mensaje ("normal", "error", "system").

        """
        # Determinar el color y estilo según el tipo de mensaje
        if msg_type == "error":
            # Mensajes de error en rojo
            formatted_text = (
                f"<div align='left' style='margin: 5px 0;'>"
                f"<span style='background-color: #dc3545; color: white; "
                f"padding: 6px 12px; border-radius: 15px; font-weight: bold;'>"
                f"⚠️ {text}</span></div>"
            )
        elif msg_type == "system":
            # Mensajes del sistema en azul claro
            formatted_text = (
                f"<div align='left' style='margin: 5px 0;'>"
                f"<span style='background-color: #17a2b8; color: white; "
                f"padding: 6px 12px; border-radius: 15px; font-style: italic;'>"
                f"[INFO] {text}</span></div>"
            )
        elif text.startswith("Tú:"):
            # Formato para mensajes propios (alineados a la derecha con color diferente)
            formatted_text = (
                f"<div align='right' style='margin: 5px 0;'>"
                f"<span style='background-color: #4361ee; color: white; "
                f"padding: 6px 12px; border-radius: 15px;'>"
                f"{text}</span></div>"
            )
        else:
            # Formato para mensajes de otros jugadores
            formatted_text = self._format_user_message(text)

        # Añadir el mensaje formateado
        self.text_field.append(formatted_text)

        # Desplazar automáticamente hacia abajo para mostrar el mensaje más reciente
        self.text_field.verticalScrollBar().setValue(
            self.text_field.verticalScrollBar().maximum()
        )

    def _format_user_message(self, text: str) -> str:
        """Formatea un mensaje de usuario aplicando el color del jugador al nombre.

        Returns:
            Mensaje formateado con el color aplicado.

        """
        # Extraer el nombre de usuario del mensaje (formato: "username: mensaje")
        if ":" in text:
            username, message = text.split(":", 1)
            username = username.strip()
            message = message.strip()

            # Obtener el color del usuario
            user_color = self._get_user_color(username)

            if user_color:
                # Formatear con el color del usuario para el nombre
                formatted_text = (
                    f"<div align='left' style='margin: 5px 0;'>"
                    f"<span style='background-color: #e9ecef; color: #212529; "
                    f"padding: 6px 12px; border-radius: 15px;'>"
                    f"<span style='color: {user_color}; font-weight: bold;'>"
                    f"{username}</span>: {message}"
                    f"</span></div>"
                )
            else:
                # Formato por defecto si no se encuentra el color
                formatted_text = (
                    f"<div align='left' style='margin: 5px 0;'>"
                    f"<span style='background-color: #e9ecef; color: #212529; "
                    f"padding: 6px 12px; border-radius: 15px;'>"
                    f"{text}</span></div>"
                )
        else:
            # Formato por defecto si no hay ":" en el mensaje
            formatted_text = (
                f"<div align='left' style='margin: 5px 0;'>"
                f"<span style='background-color: #e9ecef; color: #212529; "
                f"padding: 6px 12px; border-radius: 15px;'>"
                f"{text}</span></div>"
            )

        return formatted_text

    def _get_user_color(self, username: str) -> str | None:
        """Obtiene el color hexadecimal del usuario.

        Returns:
            Color hexadecimal del usuario o None si no se encuentra.

        """
        try:
            # Acceder a los colores asignados desde la ventana principal
            colores_asignados = self.main_window.colores.colores_asignados()

            if not colores_asignados:
                return None

            # Crear un mapeo simple basado en el hash del nombre de usuario
            # para asignar consistentemente el mismo color al mismo usuario
            user_colors = list(colores_asignados.values())
            if user_colors:
                # Usar hash del nombre para seleccionar un color consistente
                color_index = hash(username) % len(user_colors)
                selected_color = user_colors[color_index]

                # Convertir QColor a hexadecimal
                if hasattr(selected_color, "name"):
                    name_result = selected_color.name()
                    if isinstance(name_result, str):
                        return name_result  # Método de QColor para obtener hex
                if hasattr(selected_color, "red"):
                    # Fallback: convertir RGB a hex manualmente
                    r = int(selected_color.red() * 255)
                    g = int(selected_color.green() * 255)
                    b = int(selected_color.blue() * 255)
                    return f"#{r:02x}{g:02x}{b:02x}"

        except (AttributeError, KeyError, TypeError):
            # Error específico al acceder a colores o convertir QColor
            pass
        return None  # Sin color, usar formato por defecto
