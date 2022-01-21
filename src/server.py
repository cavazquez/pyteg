#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json


def client(conn, clients):
    username_str = conn.recv(1024).decode()
    username_json = json.loads(username_str)
    if 'username' in username_json:
        username = username_json['username']
        print(conn, "username = ", username)
    while True:
        data_b_r = conn.recv(1024)
        data_r = data_b_r.decode()
        data_json_r = json.loads(data_r)

        if 'chat' in data_json_r:
            for c in clients:
                if conn != c:
                    msg = username + ': ' + data_json_r['chat']
                    data_json_s = json.dumps({'chat': msg})
                    c.sendall(data_json_s.encode())


def main():
    host = '127.0.0.1'  # Standard loopback interface address (localhost)
    port = 65432  # Port to listen on (non-privileged ports are > 1023)

    clients = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        print('host:',host,'port:',port)
        while True:
            try:
                s.listen()
                conn, addr = s.accept()
                print('Connected by', addr)
                clients.append(conn)
                t = threading.Thread(target=client, args=[conn, clients])
                t.start()
            except KeyboardInterrupt:
                s.shutdown(socket.SHUT_RDWR)
                break


if __name__ == '__main__':
    main()
