import socket
import threading

from src.server_build_client import ServerBuildClient
from src.server_client_connection import ConnectionServer


def registrar_jugadores(server):
    print("Esperando jugadores...")
    host, port = "127.0.0.1", 65432
    print(f"Host: {host}, Port: {port}")
    vivo = True
    server_build_client = ServerBuildClient()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        while vivo:
            try:
                s.listen()
                conn, addr = s.accept()
                print("Connected by", addr)
                connection = ConnectionServer(conn, addr)
                user_id, client = server_build_client.build(connection, server)
                server.registrar_cliente(user_id, client)
                threading.Thread(target=client.run, args=[]).start()

            except Exception as e:
                print(e)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                vivo = False
