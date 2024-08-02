from PySide6.QtCore import QSize
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

        self.setFixedSize(QSize(1024, 200))
        layout = QVBoxLayout()
        layout.setSpacing(1)

        self.input_field = QLineEdit()
        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)

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
