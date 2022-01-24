#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json
import time
import sys
import signal



class Connection:

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


class ServerListen:

    def __init__(self):
        host = '127.0.0.1'  
        port = 65432 
        print(host, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((host, port))
        self._esperando_jugadores = True
        self._conns = []

    def registrar_jugadores(self):
        print('Esperando jugadores...')
        while self._esperando_jugadores:
            try:
                self._socket.listen()
                conn, addr = self._socket.accept()
                print('Connected by', addr)
                connection = Connection(conn, addr)
                threading.Thread(target=client, args=[connection, self]).start()
                self.registrar_conexion(connection)


                if self.cant_clients() == 1:
                    self._esperando_jugadores = False

            except Exception as e:
                print(e)
                exit(1)

    def cant_clients(self):
        return len(self._conns)

    def registrar_conexion(self, conn):
        self._conns.append(conn)


    def send_all(self, data, ignore_conn=None):
        for conn in self._conns:
            if ignore_conn != conn:
                conn.send(data, conn)

    def send(self, data, conn):
        conn.send(data)

    def close_connections(self):
        for conn in self._conns:
            print("Removiendo:",conn)
            self._conns.remove(conn)
            conn.close()


def client(conn, server_listen):
    username_set = False
    username = ""
    vivo = True
    while vivo:
        data = conn.receiver()

        if not data:
            vivo = False
            continue

        data_json_r = json.loads(data)

        if 'username' in data_json_r and not username_set:
            username = data_json_r['username']
            print("username = ", username)
            username_set = True

        if 'chat' in data_json_r:
            msg = username + ': ' + data_json_r['chat']
            data_json_s = json.dumps({'chat': msg})
            server_listen.send_all(data_json_s, ignore_conn=conn)


def main():

    clients = []

    server_listen = ServerListen()
    thread = server_listen.registrar_jugadores()

    loop = True
    while loop:
        print("Entrando en un loop")
        time.sleep(2)
        loop = False

    server_listen.close_connections()
    print("Cerrando")



if __name__ == '__main__':
    main()
