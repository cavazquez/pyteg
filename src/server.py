#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json


def client(conn, clients):
    while True:
        data_b = conn.recv(1024)
        data = data_b.decode()
        data_json = json.loads(data)

        if 'chat' in data_json:
            for c in clients:
                if conn != c:
                    c.sendall(data_b)


def main():
    host = '127.0.0.1'  # Standard loopback interface address (localhost)
    port = 65432  # Port to listen on (non-privileged ports are > 1023)

    clients = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        print('host:',host,'port:',port)
        while True:
            s.listen()
            conn, addr = s.accept()
            print('Connected by', addr)
            clients.append(conn)
            t = threading.Thread(target=client, args=[conn, clients])
            t.start()


if __name__ == '__main__':
    main()
