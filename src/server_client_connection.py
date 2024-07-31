import socket

from src.codecs import Utf8


class ConnectionServer:
    def __init__(self, connection, addr):
        self._conn = connection
        self._addr = addr

    def receiver(self):
        try:
            encode_data = self._conn.recv(1024)
            return Utf8.decode(encode_data)
        except ConnectionResetError:
            return None
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except Exception as ex:
            print("Exception:", ex)

    def send(self, data):
        encode_data = Utf8.encode(data)
        try:
            self._conn.sendall(encode_data)
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except Exception as ex:
            print("Exception:", ex)

    def close(self):
        self._conn.shutdown(socket.SHUT_RDWR)
        self._conn.close()
