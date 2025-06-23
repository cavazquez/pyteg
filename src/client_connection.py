import json

from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QMessageBox, QWidget

from src.client_tasks_manager import ClientTaskManager
from src.client_transmisor import ClientTransmisor
from src.codecs_utils import Utf8


class ConnectionClient(QWidget):
    def __init__(self, main_window, host="127.0.0.1", port=65432, username="Usuario"):
        super().__init__()
        self._host = host
        self._port = port
        self._username = username
        self._main_window = main_window
        self._socket = QTcpSocket()
        self._socket.readyRead.connect(self.read_data)
        self._socket.errorOccurred.connect(self.display_error)
        self._socket.stateChanged.connect(self.on_state_changed)
        self._socket.connected.connect(self.on_connected)
        self._transmisor = None

    def conectar(self):
        self._socket.connectToHost(self._host, self._port)
        print(f"Conectando a {self._host}:{self._port}...")

    def on_connected(self):
        print(f"Conectado a {self._host}:{self._port}")
        # Configurar el transmisor

        self._transmisor = ClientTransmisor(self)

        # Enviar el nombre de usuario al servidor después de conectarse
        if self._username:
            self._transmisor.set_username(self._username)

    def esta_conectado(self):
        print("Estoy conectado?")
        print(f"{self._socket.state()}")
        return self._socket.state() == QAbstractSocket.ConnectedState

    def send_data(self, data):
        print(f"Enviando {data}")
        encode_data = Utf8.encode(data)
        self._socket.write(encode_data)

    def read_data(self):
        data_json = ""
        while self._socket.bytesAvailable():
            encode_datas = self._socket.readAll()
            datas = Utf8.decode(encode_datas)
            print(f"Recibido data: {datas} \n longitud: {len(datas)}")
            for data in datas.split("\0"):
                print(f"data: {data}")
                if data:
                    data_json = json.loads(data)
                    print(f"Recibido {data_json}")
                    task = ClientTaskManager.msg_to_task(data_json)
                    task.run(self._main_window)

    def on_state_changed(self, state):
        if state == QAbstractSocket.HostLookupState:
            print("Resolviendo el nombre del host...")
        elif state == QAbstractSocket.ConnectingState:
            print("Conectando...")
        elif state == QAbstractSocket.ConnectedState:
            print("Conectado.")
            self._main_window.transmisor = ClientTransmisor(self)
            self._main_window.ventana_conectar.close()
        elif state == QAbstractSocket.UnconnectedState:
            print("Desconectado.")
        else:
            print(f"Estado desconocido: {state}")

    def display_error(self):
        if self._socket.errorString() == "Connection refused":
            QMessageBox.warning(self, "Advertencia", "conexión rehusada.")
        print(f"Error: {self._socket.errorString()}")
