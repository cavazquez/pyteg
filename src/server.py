#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading


def client(conn, clients):
    while True:
        data = conn.recv(1024)
        for c in clients:
            if conn != c:
                c.sendall(data)


def main():
    host = '127.0.0.1'  # Standard loopback interface address (localhost)
    port = 65432  # Port to listen on (non-privileged ports are > 1023)

    clients = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        while True:
            s.listen()
            conn, addr = s.accept()
            print('Connected by', addr)
            clients.append(conn)
            t = threading.Thread(target=client, args=[conn, clients])
            t.start()


if __name__ == '__main__':
    main()
