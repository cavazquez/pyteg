import socket

from src.codecs_utils import Utf8


class ConnectionServer:
    def __init__(self, connection, addr):
        self._conn = connection
        self._addr = addr

    def receiver(self):
        data = ""
        try:
            encode_data = self._conn.recv(1024)
            data = Utf8.decode(encode_data)
            print(f"Recibiendo {data}")
        except ConnectionResetError:
            return None
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)
        return data.split("\0")

    def send(self, data):
        print(f"Enviando {data}")
        encode_data = Utf8.encode(data + "\0")
        try:
            self._conn.sendall(encode_data)
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)

    def close(self):
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
            self._conn.close()
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)
