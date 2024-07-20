import json
import sys

from PySide6.QtWidgets import QApplication

from src.gui import Gui


class Client:
    def __init__(self):
        self._mapa = ""
        self._conexion = None
        self._username = None

    def conectar(self):
        self._conexion.conectar()
        self.obtener_username()

    def is_connected(self):
        return self._conexion.is_connected()

    def obtener_username(self):
        msg = json.dumps({"mensaje": "obtener_username"})
        self._conexion.send_data(msg)

    def set_username(self, username):
        self._username = username

    def agregar_unidades(self, cantidad):
        msg = json.dumps(
            {"mensaje": "agregar", "pais": "Circulo", "unidades": cantidad},
        )
        self._conexion.send_data(msg)

    def send_chat(self, text):
        msg = json.dumps({"mensaje": "chat", "chat": text})
        self._conexion.send_data(msg)

    def get_data(self):
        return self._conexion.get_data()

    def cerrar(self):
        msg = json.dumps({"mensaje": "cerrar"})
        print("Enviando mensaje de cierre")
        self._conexion.send_data(msg)
        self._conexion.close()


def main():
    client = Client()
    app = QApplication()
    gui = Gui(client)

    # tr = Transceiver(client, gui)
    # t = Thread(target=tr.receiver, args=[])
    # t.start()

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
