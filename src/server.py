#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json
import toml


def build_mapa():
    with open('paises.toml') as f:
        toml_string = f.read()
        parsed_toml = toml.loads(toml_string)

    mapa = {k: [1, parsed_toml[k]['continente'], None] for k in parsed_toml}

    return mapa


def rotar_jugadores(jugadores):
    print('Rotar jugadores')
    primer_elemento = jugadores[0]
    jugadores = jugadores[1:]
    jugadores.append(primer_elemento)
    return jugadores


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

    def __init__(self, user_id, conn):
        self._user_id = user_id
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
        "chau"
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
                print("Añadiendo una unidad")
                game.agregar_una_unidad(self._user_id, data_json_r['agregar_una_unidad'])

            if 'mapa' in data_json_r:
                game.ver_mapa()

            if 'start' in data_json_r:
                game.start(server)

            if 'atacar' in data_json_r:
                atacante, defensor = data_json_r['atacar'].split()
                game.atacar(atacante, defensor)

            if 'reagrupar' in data_json_r:
                desde, hacia, cantidad = data_json_r['reagrupar'].split()
                game.reagrupar(desde, hacia, int(cantidad))

            if 'finalizar_turno' in data_json_r:
                game.ronda().finalizar_turno()


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
            client = Client(user_id, connection)
            server.registrar_cliente(user_id, client)
            threading.Thread(target=client.run, args=[server, game]).start()
            user_id += 1

        except Exception as e:
            print(e)
            exit(1)
