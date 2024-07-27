import sys

from PySide6.QtWidgets import QApplication

from src.gui import Gui


class Client:
    def __init__(self):
        self._mapa = ""
        self._conexion = None
        self._username = None


def main():
    client = Client()
    app = QApplication()
    gui = Gui(client)

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
