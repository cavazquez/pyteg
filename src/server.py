#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
from src.game import Game
from src.server_client import Client, ConnectionServer


class Server:
    def __init__(self):
        self._clients = dict()

    def cant_clients(self):
        return len(self._clients)

    def registrar_cliente(self, user_id, client):
        self._clients[user_id] = client

    def send_all(self, data, ignore_conn=None):
        print("clients: ", type(self._clients))
        for _, client in self._clients.items():
            if ignore_conn != client:
                client.send(data)

    def send(self, client, data):
        client.send(data)

    def dame_lista_jugadores(self):
        return list(self._clients.keys())


def registrar_jugadores(server, game):
    user_id = 1
    print("Esperando jugadores...")
    host = "127.0.0.1"
    port = 65432
    print(host, port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        while True:
            try:
                s.listen()
                conn, addr = s.accept()
                print("Connected by", addr)
                connection = ConnectionServer(conn, addr)
                client = Client(user_id, connection)
                server.registrar_cliente(user_id, client)
                threading.Thread(target=client.run, args=[server, game]).start()
                user_id += 1

            except Exception as e:
                print(e)
                exit(1)


def main():
    server = Server()
    game = Game(server)
    registrar_jugadores(server, game)
    # server_th = threading.Thread(target=registrar_jugadores, args=[server, game])
    # server_th.start()


if __name__ == "__main__":
    main()
