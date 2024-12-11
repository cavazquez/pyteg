import sys

from PySide6.QtWidgets import QApplication

from src.gui import Gui


class Client:
    def __init__(self):
        self._mapa = ""
        self._username = None
        self._userid = None

    def set_username(self, username):
        self._username = username

    def set_userid(self, userid):
        self._userid = userid

    def username(self):
        return self._username

    def userid(self):
        return self._userid


def main():
    client = Client()
    app = QApplication()
    gui = Gui(client)

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
