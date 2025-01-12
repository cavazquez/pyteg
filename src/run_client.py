import sys

from PySide6.QtWidgets import QApplication

from src.client import Client
from src.gui import Gui


def main():
    client = Client()
    app = QApplication(sys.argv)
    gui = Gui(client)

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
