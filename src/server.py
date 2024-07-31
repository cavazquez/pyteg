import socket
import sys
import threading

from src.build_mapa import build_mapa
from src.game import Game
from src.mapa import Mapa
from src.server_client import Client
from src.server_client_connection import ConnectionServer


class Server:
    def __init__(self):
        self._clients = {}

    def cant_clients(self):
        return len(self._clients)

    def quitarme(self, user_id):
        print(f"Quitando {user_id}")
        self._clients.pop(user_id)

    def registrar_cliente(self, user_id, client):
        self._clients[user_id] = client

    def send_all(self, data, ignore_conn=None):
        for user_id, client in self._clients.items():
            print(user_id, client)
        for _, client in self._clients.values():
            if ignore_conn != client:
                print("send_all:", data)
                client.send(data)

    def send(self, client, data):
        client.send(data)

    def dame_lista_jugadores(self):
        return list(self._clients.keys())

    def dame_clientes(self):
        return self._clients.values()


def registrar_jugadores(server, game):
    user_id = 1
    print("Esperando jugadores...")
    host = "127.0.0.1"
    port = 65432
    print(host, port)
    usernames = ["Cortazar", "Borges", "Sabato", "Arlt", "Bioy", "Saer"]
    vivo = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        while vivo:
            try:
                s.listen()
                conn, addr = s.accept()
                print("Connected by", addr)
                connection = ConnectionServer(conn, addr)

                client = Client(user_id, connection, server, usernames[user_id])
                server.registrar_cliente(user_id, client)
                threading.Thread(target=client.run, args=[game]).start()
                user_id += 1

            except Exception as e:
                print(e)
                sys.exit(1)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                vivo = False


def main():
    server = Server()
    mapa = Mapa(build_mapa)
    game = Game(mapa, None)
    registrar_jugadores(server, game)


if __name__ == "__main__":
    main()
