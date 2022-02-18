#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json
import time
import sys

class Game:

    def __init__(self, mapa):
        self._mapa = mapa

    def agregar_una_unidad(self, pais):
        print(self._mapa)
        self._mapa[pais] += 1
        print(self._mapa)


class ConnectionServer:

    def __init__(self, connection, addr):
        self._conn = connection
        self._addr = addr

    def receiver(self):
        data_r = self._conn.recv(1024).decode()
        return data_r

    def send(self, data):
        self._conn.sendall(data.encode())

    def close(self):
        self._conn.shutdown(socket.SHUT_RDWR)
        self._conn.close()



class Client:

    def __init__(self, conn):
        self._conn = conn

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def run(self, server, game):
        username_set = False
        username = ""
        vivo = True
        estado_global = "chau"
        while vivo:
            data = self.receiver()

            if not data:
                vivo = False
                continue

            data_json_r = json.loads(data)

            if 'username' in data_json_r and not username_set:
                username = data_json_r['username']
                print("username = ", username)
                username_set = True

            if 'chat' in data_json_r:
                print("Enviando mensaje de chat")
                msg = username + ': ' + data_json_r['chat']
                data_json_s = json.dumps({'chat': msg})
                server.send_all(data_json_s, ignore_conn=self._conn)

            if 'agregar_una_unidad' in data_json_r:
                print("Añandiendo una unidad")
                game.agregar_una_unidad(data_json_r['agregar_una_unidad'])

class Server:

    def __init__(self):
        self._clients = []

    def cant_clients(self):
        return len(self._conns)

    def registrar_cliente(self, client):
        self._clients.append(client)


    def send_all(self, data, ignore_conn=None):
        for client in self._clients:
            if ignore_conn != client:
                client.send(data)

    def send(self, client, data):
        client.send(data)

    def start(self):
        print("Empezando partida")
        client = self._clients[0]

        mapa = {'asd':'Kamchatka', 'exactas':'Francia'}
        data_j = json.dumps({'mapa': mapa})
        self.send(client, data_j)

    def close_connections(self):
        for conn in self._conns:
            print("Removiendo:",conn)
            self._conns.remove(conn)
            conn.close()


def registrar_jugadores(server, game):
    print('Esperando jugadores...')
    host = '127.0.0.1'  
    port = 65432 
    print(host, port)
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind((host, port))
    while True:
        try:
            socket_server.listen()
            conn, addr = socket_server.accept()
            print('Connected by', addr)
            connection = ConnectionServer(conn, addr)
            client = Client(connection)
            server.registrar_cliente(client)
            threading.Thread(target=client.run, args=[server, game]).start()

        except Exception as e:
            print(e)
            exit(1)
