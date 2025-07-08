from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class Chat(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # Área de mensajes
        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.text_field.setMinimumHeight(150)

        # Contenedor para el input y el botón
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)

        # Campo de entrada de texto
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe un mensaje...")
        self.input_field.returnPressed.connect(self.send_message)

        # Botón de enviar
        self.send_button = QPushButton("Enviar")
        self.send_button.setFixedSize(60, 30)
        self.send_button.setToolTip("Enviar mensaje")
        self.send_button.clicked.connect(self.send_message)

        # Agregar widgets al layout de entrada
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        # Agregar widgets al layout principal
        main_layout.addWidget(self.text_field)
        main_layout.addWidget(input_container)

        # Establecer el layout principal
        self.setLayout(main_layout)

    def setup_styles(self):
        # Estilos generales para la ventana
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            /* Estilo del área de mensajes */
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
                color: #333;
                selection-background-color: #4CAF50;
                selection-color: white;
            }

            /* Estilo del campo de entrada */
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 13px;
                background-color: white;
                color: #333;
                min-height: 30px;
            }

            QLineEdit:focus {
                border-color: #4CAF50;
            }

            /* Estilo del botón de enviar */
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: normal;
                min-width: 60px;
                padding: 2px 8px;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }

            QPushButton:pressed {
                background-color: #3e8e41;
            }

            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

    def send_message(self):
        text = self.input_field.text()
        if text:
            self.main_window.transmisor.enviar_chat(text)
            self.input_field.clear()

    def append(self, text):
        self.text_field.append(text)
