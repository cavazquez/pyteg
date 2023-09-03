import json
import socket
import time

from PySide6.QtWidgets import QApplication

from src.gui import Gui


class Client:
    def __init__(self, connection):
        self._mapa = ""
        self._connection = connection

    def conectar(self):
        self._connection.conectar()

    def is_connected(self):
        return self._connection.is_connected()

    def send_chat(self, text):
        msg = json.dumps({"mensaje": "chat", "chat": text})
        self._connection.send_data(msg)

    def cerrar(self):
        msg = json.dumps({"mensaje": "cerrar"})
        self._connection.send_data(msg)
        self._connection.close()


class ConnectionClient:
    def __init__(self, host="127.0.0.1", port=65432):
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connected = False

    def conectar(self):
        self._socket.connect((self._host, self._port))
        self._connected = True
        print(f"Conectado con {self._host}:{self._port}")

    def close(self):
        self._socket.close()

    def is_connected(self):
        return self._connected

    def send_data(self, data):
        try:
            if self.is_connected():
                self._socket.sendall(data.encode())
            else:
                print("No conectado")
        except BrokenPipeError:
            self._connected = False

    def get_data(self):
        data = ""
        try:
            if self.is_connected():
                data = self._socket.recv(1024)
        except BrokenPipeError:
            self._connected = False
        return data


class Transceiver:
    def __init__(self, client, gui):
        self.client = client
        self.gui = gui
        self.vivo = True

    def cerrar(self):
        self.vivo = False

    def receiver(self):
        data_b = ""
        while self.vivo:
            while not self.client.is_connected():
                time.sleep(0.1)
            if self.client.is_connected():
                data_b = self.client.get_data()
                if not data_b:
                    print("socket connection broken")
                    break

            data = data_b.decode()
            data_json = json.loads(data)
            print(data_json)

            if "chat" in data_json:
                msg = data_json["chat"]
                self.gui.msg_chat(msg)
            elif "mapa" in data_json:
                self.client.update_mapa(data_json["mapa"])
            elif "jugadores" in data_json:
                self.gui.update(data_json["jugadores"])
            else:
                print("Comando no reconocido")


def main():
    connection = ConnectionClient()
    client = Client(connection)
    app = QApplication()
    gui = Gui(client)
    gui.show()

    tr = Transceiver(client, gui)

    app.exec()
    tr.receiver()
    print("BB")
    tr.cerrar()
    print("AA")


if __name__ == "__main__":
    main()
