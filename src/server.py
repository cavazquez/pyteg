#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket


def main():
    host = '127.0.0.1'  # Standard loopback interface address (localhost)
    port = 65432  # Port to listen on (non-privileged ports are > 1023)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)


if __name__ == '__main__':
    main()
