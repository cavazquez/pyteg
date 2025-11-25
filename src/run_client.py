"""Módulo principal para ejecutar el cliente del juego."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.client import Client
from src.gui import Gui
from src.version import NAME, VERSION


def main() -> None:
    """Función principal que inicia el cliente del juego."""
    print(f"{NAME} v{VERSION}")
    client = Client()
    app = QApplication(sys.argv)
    gui = Gui(client)

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
