import json
import sys
from threading import Thread

from PySide6.QtWidgets import QApplication

from src.connection_client import ConnectionClient
from src.gui import Gui
from src.transceiver import Transceiver


class Client:
    def __init__(self, connection):
        self._mapa = ""
        self._connection = connection
        self._username = None

    def conectar(self):
        self._connection.conectar()
        self.obtener_username()

    def is_connected(self):
        return self._connection.is_connected()

    def obtener_username(self):
        msg = json.dumps({"mensaje": "obtener_username"})
        self._connection.send_data(msg)

    def set_username(self, username):
        self._username = username

    def send_chat(self, text):
        msg = json.dumps({"mensaje": "chat", "chat": text})
        self._connection.send_data(msg)

    def get_data(self):
        return self._connection.get_data()

    def cerrar(self):
        msg = json.dumps({"mensaje": "cerrar"})
        print("Enviando mensaje de cierre")
        self._connection.send_data(msg)
        self._connection.close()


def main():
    connection = ConnectionClient()
    client = Client(connection)
    app = QApplication()
    gui = Gui(client)

    print("Transceiver")
    tr = Transceiver(client, gui)
    t = Thread(target=tr.receiver, args=[])
    t.start()

    print("gui show")
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
