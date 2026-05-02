"""Estilos QSS del diálogo de tarjetas (separados del cableado Qt)."""

from __future__ import annotations

# Título principal "Tarjetas Asignadas"
STYLE_TITULO_PRINCIPAL = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
        padding: 10px;
    }
"""

STYLE_BUTTON_CERRAR = """
    QPushButton {
        padding: 8px 16px;
        font-size: 12px;
        background-color: #95a5a6;
        color: white;
        border: none;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #7f8c8d;
    }
"""

STYLE_PLACEHOLDER_VACIO = """
    QLabel {
        background-color: #ecf0f1;
        border: 2px dashed #bdc3c7;
        border-radius: 8px;
        color: #7f8c8d;
        font-style: italic;
    }
"""

STYLE_TITULO_OBJETIVO = """
    QLabel {
        font-size: 14px;
        font-weight: bold;
        color: #8e44ad;
        padding: 5px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin-bottom: 5px;
    }
"""

STYLE_LABEL_OBJETIVO = """
    QLabel {
        font-size: 12px;
        color: #2c3e50;
        padding: 10px;
        background-color: #ecf0f1;
        border: 1px solid #bdc3c7;
        border-radius: 5px;
        margin: 5px;
    }
"""

STYLE_LABEL_INFO_INICIAL = """
    QLabel {
        font-size: 14px;
        font-weight: bold;
        color: #2c3e50;
        padding: 8px;
        background-color: #ecf0f1;
        border-radius: 4px;
        margin: 5px;
    }
"""

STYLE_BUTTON_SELECCIONAR_TODAS = """
    QPushButton {
        padding: 8px 16px;
        font-size: 12px;
        background-color: #f39c12;
        color: white;
        border: none;
        border-radius: 4px;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #d68910;
    }
"""

STYLE_BUTTON_DESELECCIONAR_TODAS = """
    QPushButton {
        padding: 8px 16px;
        font-size: 12px;
        background-color: #95a5a6;
        color: white;
        border: none;
        border-radius: 4px;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #7f8c8d;
    }
"""

STYLE_BUTTON_RECLAMAR = """
    QPushButton {
        padding: 10px 20px;
        font-size: 14px;
        background-color: #27ae60;
        color: white;
        border: none;
        border-radius: 5px;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #229954;
    }
    QPushButton:disabled {
        background-color: #95a5a6;
    }
"""

STYLE_BUTTON_CANJE = """
    QPushButton {
        padding: 10px 20px;
        font-size: 14px;
        background-color: #e74c3c;
        color: white;
        border: none;
        border-radius: 5px;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #c0392b;
    }
    QPushButton:disabled {
        background-color: #95a5a6;
    }
"""


def style_label_info_seleccion(color: str) -> str:
    """Estilo del contador de selección según color de fondo.

    Returns:
        Hoja de estilo QSS para el ``QLabel`` del contador.

    """
    return f"""
        QLabel {{
            font-size: 14px;
            font-weight: bold;
            color: white;
            padding: 8px;
            background-color: {color};
            border-radius: 4px;
            margin: 5px;
        }}
    """
