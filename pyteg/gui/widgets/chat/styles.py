"""Hojas de estilo (QSS) usadas por el widget de chat."""

from __future__ import annotations

CHAT_STYLESHEET = """
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
"""
