import argparse
import json
import random
import socket
import threading
import time

# from server import Server, registrar_jugadores
# from game import Game
from gui import Gui
from PySide6.QtWidgets import QApplication


class Client:
    def __init__(self):
        self._mapa = ""

    def update_mapa(self, state):
        print("Actualizando mapa")
        print(f"mapa: {self._mapa}")
        self._mapa = state
        print(f"mapa: {self._mapa}")


class ConnectionClient:
    def __init__(self, host="127.0.0.1", port=65432):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        print(f"Conectado con {host}:{port}")
        self._connected = True

    def is_connected(self):
        return self._connected

    def send_data(self, data):
        try:
            self._socket.sendall(data)
        except BrokenPipeError:
            self._connected = False

    def get_data(self):
        data = ""
        try:
            data = self._socket.recv(1024)
        except BrokenPipeError:
            self._connected = False
        return data


class Transceiver:
    @staticmethod
    def receiver(connection, client, gui):
        data_b = ""
        while connection.is_connected():
            data_b = connection.get_data()
            if not data_b:
                print("socket connection broken")
                break

            data = data_b.decode()
            data_json = json.loads(data)

            if "chat" in data_json:
                print(data_json["chat"])
            elif "mapa" in data_json:
                client.update_mapa(data_json["mapa"])
            elif "jugadores" in data_json:
                gui.update(data_json["jugadores"])
            else:
                print("Comando no reconocido")

    @staticmethod
    def sender(connection):
        numero = random.randint(1, 10)
        username = f"cliente-{numero}"
        username_data = json.dumps({"username": username})
        connection.send_data(username_data.encode())
        while connection.is_connected():
            data = input("")

            if data.startswith("chat"):
                data = data[len("chat") :]
                json_data = json.dumps({"chat": data})
                connection.send_data(json_data.encode())
            elif data.startswith("start"):
                json_data = json.dumps({"start": ""})
                connection.send_data(json_data.encode())
            elif data.startswith("agregar"):
                data = data[len("agregar") :]
                json_data = json.dumps({"agregar_una_unidad": data})
                connection.send_data(json_data.encode())
            elif data.startswith("atacar"):
                data = data[len("atacar") :]
                json_data = json.dumps({"atacar": data})
                connection.send_data(json_data.encode())
            elif data.startswith("reagrupar"):
                data = data[len("reagrupar") :]
                json_data = json.dumps({"reagrupar": data})
                connection.send_data(json_data.encode())
            elif data.startswith("mapa"):
                json_data = json.dumps({"mapa": ""})
                connection.send_data(json_data.encode())
            elif data.startswith("finalizar_turno"):
                json_data = json.dumps({"finalizar_turno": ""})
                connection.send_data(json_data.encode())
            else:
                print("Error: Comando desconocido")


def main():
    parser = argparse.ArgumentParser(description="PyTeg")
    parser.add_argument("--server", action="store_true", help="Iniciar servidor")

    parser.parse_args()

    app = QApplication()
    gui = Gui()
    gui.show()

    # if vars(args)['server']:
    #    print('Iniciando Server')
    #    server = Server()
    #    game = Game(server)
    #    server_th = threading.Thread(target=registrar_jugadores, args=[server, game])
    #    server_th.start()

    # Espero a que se inicie el servidor
    time.sleep(0.5)

    client = Client()
    connection = ConnectionClient()
    receiver_th = threading.Thread(
        target=Transceiver.receiver, args=[connection, client, gui]
    )
    receiver_th.start()
    sender_th = threading.Thread(target=Transceiver.sender, args=[connection])
    sender_th.start()

    app.exec()

    receiver_th.join()
    sender_th.join()


if __name__ == "__main__":
    main()
