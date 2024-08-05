import json

from PySide6.QtNetwork import QTcpSocket

from src.client_tasks_manager import ClientTaskManager
from src.codecs import Utf8


class ConnectionClient:
    def __init__(self, main_window, host="127.0.0.1", port=65432):
        self._host = host
        self._port = port
        self._main_window = main_window
        self._socket = QTcpSocket()
        self._socket.readyRead.connect(self.read_data)
        self._socket.errorOccurred.connect(self.display_error)

    def conectar(self):
        self._socket.connectToHost(self._host, self._port)
        print(f"Conectado con {self._host}:{self._port}")

    def send_data(self, data):
        print(f"Enviando {data}")
        encode_data = Utf8.encode(data)
        self._socket.write(encode_data)

    def read_data(self):
        data_json = ""
        while self._socket.bytesAvailable():
            encode_data = self._socket.readAll()
            data = Utf8.decode(encode_data)
            data_json = json.loads(data)
            print(f"Recibido {data_json}")
            task = ClientTaskManager.msg_to_task(data_json)
            task.run(self._main_window)

    def display_error(self):
        print(f"Error: {self._socket.errorString()}")
