from PySide6.QtWidgets import (
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

        layout = QVBoxLayout()
        layout.setSpacing(1)

        self.input_field = QLineEdit()
        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        # Estilos CSS para el botón de enviar
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  /* Verde */
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;  /* Verde más oscuro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #3e8e41;  /* Verde aún más oscuro al hacer clic */
            }
        """)

        layout.addWidget(self.text_field)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        text = self.input_field.text()
        if text:
            self.main_window.transmisor.enviar_chat(text)
            self.input_field.clear()

    def append(self, text):
        self.text_field.append(text)
