#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json
import time
import sys
from random import choices

class Dados:

    @staticmethod
    def tirar_dados_ordenados(cant):
        return sorted(choices(range(1,6), k=cant), reverse=True)


class Batalla:

    @staticmethod
    def ataquen(mapa, atacante, defensor):
        cant_atacantes =  mapa.cantidad_unidades(atacante)
        cant_defensores = mapa.cantidad_unidades(defensor)

        print("cant_atacantes:", cant_atacantes)
        print("cant_defensores:", cant_defensores)

        cant_dados_atacantes = min(cant_atacantes, 3)
        cant_dados_defensores = min(cant_defensores, 3)

        print("cant_dados_atacantes:", cant_dados_atacantes)
        print("cant_dados_defensores:", cant_dados_defensores)

        dados_atacantes = Dados.tirar_dados_ordenados(cant_dados_atacantes)
        dados_defensores = Dados.tirar_dados_ordenados(cant_dados_defensores)

        print("dados_atacantes:", dados_atacantes)
        print("dados_defensores:", dados_defensores)

        for combate in range(min(len(dados_atacantes), len(dados_defensores))):
            if dados_defensores[combate] < dados_atacantes[combate]:
                cant_defensores -= 1
            else:
                cant_atacantes -= 1

        print("cant_atacantes:", cant_atacantes)
        print("cant_defensores:", cant_defensores)

        mapa.set_unidades(atacante, max(1, cant_atacantes))
        mapa.set_unidades(defensor, max(0, cant_defensores))



class PrimerTurno:

    def __init__(self, jugador):
        self._jugador = jugador
        self._unidades = 6

    def jugador_actual(self):
        return self._jugador

    def usar_unidad(self):
        self._unidades -= 1

class Mapa:

    def __init__(self):
        self._mapa = {'Argentina': 2, 'Francia': 2}

    def agregar_una_unidad(self, pais):
        self._mapa[pais] += 1

    def cantidad_unidades(self, pais):
        return self._mapa[pais]

    def set_unidades(self, pais, cant):
        self._mapa[pais] = cant

    def __str__(self):
        return json.dumps(self._mapa)

class PrimeraRonda:

    def __proximo_turno(self, jugadores):
        for turno in [ PrimerTurno(id_jugador) for id_jugador in jugadores]:
            yield turno

    def __init__(self, jugadores):
        print("Primera ronda")
        self._unidades = dict()
        self._turnos = self.__proximo_turno(jugadores)
        self._turno_actual = next(self._turnos)

    def usar_unidad(self):
        self._turno_actual.usar_unidad()
        print(self._unidades)

    def turno_actual(self):
        return self._turno_actual

class Game:

    def __init__(self, server):
        self._mapa = Mapa()
        self._start = False
        self._ronda = None
        self._jugadores = []
        self._server = server

    def agregar_una_unidad(self, jugador, pais):
        self._mapa.agregar_una_unidad(pais)
        self._ronda.usar_unidad(jugador)

    def start(self):
        self._jugadores = self._server.dame_jugadores()
        print("jugadores: ", self._jugadores)
        self._ronda = PrimeraRonda(self._jugadores)
        self._start = True
        print(self._ronda.turno_actual().jugador_actual())

    def ver_mapa(self):
        print(self._mapa)

    def atacar(self, atacante, defensor):
        Batalla.ataquen(self._mapa, atacante, defensor)



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
                print("Añadiendo una unidad")
                game.agregar_una_unidad(self._user_id, data_json_r['agregar_una_unidad'])

            if 'mapa' in data_json_r:
                game.ver_mapa()

            if 'start' in data_json_r:
                game.start()

            if 'atacar' in data_json_r:
                atacante, defensor = data_json_r['atacar'].split()
                
                game.atacar(atacante, defensor)

class Server:

    def __init__(self):
        self._clients = dict()

    def cant_clients(self):
        return len(self._clients)

    def registrar_cliente(self, user_id, client):
        self._clients[user_id] = client


    def send_all(self, data, ignore_conn=None):
        for _ , client in self._clients:
            if ignore_conn != client:
                client.send(data)

    def send(self, client, data):
        client.send(data)

    def dame_jugadores(self):
        return self._clients.keys()

    def close_connections(self):
        for conn in self._clients:
            print("Removiendo:",conn)
            self._conns.remove(conn)
            conn.close()


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
