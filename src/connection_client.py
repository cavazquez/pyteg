import logging
import socket

logging.basicConfig(filename="example.log", encoding="utf-8", level=logging.DEBUG)


class ConnectionClient:
    def __init__(self, host="127.0.0.1", port=65432):
        logging.info("Creando ConnectionClient")
        self._host = host
        self._port = port
        self._socket = None  # socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def conectar(self):
        logging.info("Conectando")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))
        print(f"Conectado con {self._host}:{self._port}")

    def close(self):
        logging.info("Cerrando Socket")
        print("Cerrando Socket")
        if self.is_connected():
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()

    def is_connected(self):
        logging.info("Consultando si está conectado")
        print("Consultando si está conectado")
        try:
            if self._socket:
                self._socket.recv(1024, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            else:
                print("Socket es None")
                return False
        except ConnectionResetError as e:
            print("ConnectionResetError")
            print(e)
            return False
        except OSError:
            return True
        except BlockingIOError as e:
            print("BlockingIOError")
            print(e)
            return True
        except Exception as e:
            print(e)
            return False

        print("SI, esta conectado")
        return True

    def send_data(self, data):
        logging.info("Send Data")
        try:
            if self.is_connected():
                self._socket.sendall(data.encode())
            else:
                print("No conectado")
        except BrokenPipeError as e:
            print(e)

    def get_data(self):
        logging.info("Get Data")
        data = ""
        try:
            if self.is_connected():
                data = self._socket.recv(1024)
        except BrokenPipeError:
            self._connected = False
        return data
