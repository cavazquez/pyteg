from __future__ import annotations

import json
from typing import Any

from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QMessageBox, QWidget

from src.client_tasks_manager import ClientTaskManager
from src.client_transmisor import ClientTransmisor
from src.codecs_utils import Utf8


class ConnectionClient(QWidget):
    def __init__(
        self,
        main_window: Any,
        host: str = "127.0.0.1",
        port: int = 65432,
        username: str = "Usuario",
    ):
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

    def conectar(self):
        self._socket.connectToHost(self._host, self._port)
        print(f"Conectando a {self._host}:{self._port}...")

    def on_connected(self):
        print(f"Conectado a {self._host}:{self._port}")
        # Reproducir sonido de conexión
        if hasattr(self._main_window, "sound_manager"):
            self._main_window.sound_manager.play_connect()
        # Actualizar estado en la interfaz
        self._main_window.update_game_state("Conectado")
        # Usar el transmisor de main_window
        self._main_window.transmisor.set_username(self._username)

    def esta_conectado(self) -> bool:
        print("Estoy conectado?")
        print(f"{self._socket.state()}")
        return self._socket.state() == QAbstractSocket.SocketState.ConnectedState

    def get_main_window(self):
        """Obtiene la ventana principal."""
        return self._main_window

    def send_data(self, data):
        print(f"Enviando {data}")
        # Agregar separador \0 al final del mensaje
        encode_data = Utf8.encode(data + "\0")
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
                    # Verificar si es un mensaje de rechazo (texto plano)
                    if "El juego ya está en progreso" in data:
                        print(f"Servidor rechazó la conexión: {data}")
                        QMessageBox.warning(
                            self._main_window, "Conexión rechazada", data
                        )
                        self._socket.disconnectFromHost()
                        return

                    try:
                        data_json = json.loads(data)
                        print(f"Recibido {data_json}")
                        task = ClientTaskManager.msg_to_task(data_json)
                        task.run(self._main_window)
                    except json.JSONDecodeError:
                        print(f"Mensaje no JSON recibido: {data}")
                        # Podría ser un mensaje de rechazo u otro tipo de mensaje
                        if data.strip():  # Si no está vacío
                            QMessageBox.warning(
                                self._main_window, "Mensaje del servidor", data
                            )

    def on_state_changed(self, state: QAbstractSocket.SocketState) -> None:
        if state == QAbstractSocket.SocketState.HostLookupState:
            print("Resolviendo el nombre del host...")
        elif state == QAbstractSocket.SocketState.ConnectingState:
            print("Conectando...")
        elif state == QAbstractSocket.SocketState.ConnectedState:
            print("Conectado.")
            self._main_window.transmisor = ClientTransmisor(self)
            self._main_window.ventana_conectar.close()
            # Actualizar estado de botones en la toolbar
            if hasattr(self._main_window, "toolbar"):
                self._main_window.toolbar.actualizar_estado_conexion(conectado=True)
        elif state == QAbstractSocket.SocketState.UnconnectedState:
            print("Desconectado.")
            # Reproducir sonido de desconexión
            if hasattr(self._main_window, "sound_manager"):
                self._main_window.sound_manager.play_disconnect()
            self._main_window.update_game_state("Desconectado")
            # Actualizar estado de botones en la toolbar
            if hasattr(self._main_window, "toolbar"):
                self._main_window.toolbar.actualizar_estado_conexion(conectado=False)
        else:
            print(f"Estado desconocido: {state}")

    def desconectar(self) -> None:
        """Desconecta el cliente del servidor."""
        if self._socket.state() == QAbstractSocket.SocketState.ConnectedState:
            self._socket.disconnectFromHost()
            print("Desconectando del servidor...")

    def display_error(self):
        if self._socket.errorString() == "Connection refused":
            QMessageBox.warning(self, "Advertencia", "conexión rehusada.")
        print(f"Error: {self._socket.errorString()}")
