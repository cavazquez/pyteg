"""Hojas de estilo (QSS) usadas por el diálogo de conexión."""

from __future__ import annotations

TITLE_LABEL_STYLE = """
    font-size: 16px;
    font-weight: bold;
    color: #212529;
    margin-bottom: 5px;
"""

DESC_LABEL_STYLE = """
    font-size: 12px;
    color: #6c757d;
    margin-bottom: 10px;
"""

FORM_LABEL_STYLE = "font-weight: bold; color: #495057; font-size: 13px;"

INPUT_STYLE = """
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

CANCEL_BUTTON_STYLE = """
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
"""

CONNECT_BUTTON_STYLE = """
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
"""

DIALOG_STYLE = """
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
"""

ERROR_BOX_STYLE = """
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
"""
