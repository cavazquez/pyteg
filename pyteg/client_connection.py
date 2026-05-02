"""Módulo para manejar la conexión del cliente al servidor."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QMessageBox, QWidget

from pyteg.client.tasks.manager import ClientTaskManager
from pyteg.client_transmisor import ClientTransmisor
from pyteg.codecs_utils import Utf8
from pyteg.i18n import translate as _
from pyteg.logger import get_logger

_LOG = get_logger("client.connection")


class ConnectionClient(QWidget):
    """Widget que maneja la conexión TCP del cliente al servidor."""

    def __init__(
        self,
        main_window: Any,
        host: str = "127.0.0.1",
        port: int = 65432,
        username: str = "Usuario",
    ) -> None:
        """Inicializa la conexión del cliente.

        Args:
            main_window: Ventana principal de la aplicación.
            host: Dirección IP del servidor.
            port: Puerto del servidor.
            username: Nombre de usuario del cliente.

        """
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

    def conectar(self) -> None:
        """Establece la conexión con el servidor."""
        self._socket.connectToHost(self._host, self._port)
        _LOG.info("Conectando a %s:%s...", self._host, self._port)

    def on_connected(self) -> None:
        """Maneja el evento de conexión exitosa al servidor."""
        _LOG.info("Conectado a %s:%s", self._host, self._port)
        # Reproducir sonido de conexión
        if hasattr(self._main_window, "sound_manager"):
            self._main_window.sound_manager.play_connect()
        # Actualizar estado en la interfaz
        self._main_window.update_game_state("Conectado")
        # Usar el transmisor de main_window
        self._main_window.transmisor.set_username(self._username)

    def esta_conectado(self) -> bool:
        """Verifica si el cliente está conectado al servidor.

        Returns:
            True si está conectado, False en caso contrario.

        """
        connected = self._socket.state() == QAbstractSocket.SocketState.ConnectedState
        _LOG.debug("Socket state=%s connected=%s", self._socket.state(), connected)
        return connected

    def get_main_window(self) -> Any:
        """Obtiene la ventana principal.

        Returns:
            La ventana principal del cliente.

        """
        return self._main_window

    def send_data(self, data: str) -> None:
        """Envía datos al servidor.

        Args:
            data: Datos a enviar como string.

        """
        _LOG.debug("Enviando mensaje (%s bytes)", len(data))
        # Agregar separador \0 al final del mensaje
        encode_data = Utf8.encode(data + "\0")
        self._socket.write(encode_data)

    def read_data(self) -> None:
        """Lee datos recibidos del servidor."""
        while self._socket.bytesAvailable():
            encode_datas = self._socket.readAll()
            datas = Utf8.decode(bytes(encode_datas))
            _LOG.debug(
                "Recibido chunk (%s caracteres)",
                len(datas),
            )
            for data in datas.split("\0"):
                if data:
                    _LOG.debug("Fragmento recibido (%s bytes)", len(data))
                    # Verificar si es un mensaje de rechazo (texto plano)
                    if "El juego ya está en progreso" in data:
                        _LOG.warning("Servidor rechazó la conexión: %s", data)
                        QMessageBox.warning(
                            self._main_window,
                            _("Conexión rechazada"),
                            data,
                        )
                        self._socket.disconnectFromHost()
                        return

                    try:
                        data_json = json.loads(data)
                        _LOG.debug("JSON recibido: %s", data_json.get("mensaje"))
                        task = ClientTaskManager.msg_to_task(data_json)
                        task.run(self._main_window)
                    except json.JSONDecodeError:
                        _LOG.warning("Mensaje no JSON: %s", data[:200])
                        # Podría ser un mensaje de rechazo u otro tipo de mensaje
                        if data.strip():  # Si no está vacío
                            QMessageBox.warning(
                                self._main_window,
                                _("Mensaje del servidor"),
                                data,
                            )

    def on_state_changed(self, state: QAbstractSocket.SocketState) -> None:
        """Maneja los cambios de estado de la conexión.

        Args:
            state: Nuevo estado del socket.

        """
        if state == QAbstractSocket.SocketState.HostLookupState:
            _LOG.debug("Resolviendo nombre de host...")
        elif state == QAbstractSocket.SocketState.ConnectingState:
            _LOG.debug("Conectando...")
        elif state == QAbstractSocket.SocketState.ConnectedState:
            _LOG.info("Socket en estado conectado")
            self._main_window.transmisor = ClientTransmisor(self)
            self._main_window.ventana_conectar.close()
            # Actualizar estado de botones en la toolbar
            if hasattr(self._main_window, "toolbar"):
                self._main_window.toolbar.actualizar_estado_conexion(conectado=True)
        elif state == QAbstractSocket.SocketState.UnconnectedState:
            _LOG.info("Socket desconectado")
            # Reproducir sonido de desconexión
            if hasattr(self._main_window, "sound_manager"):
                self._main_window.sound_manager.play_disconnect()
            self._main_window.update_game_state("Desconectado")
            # Actualizar estado de botones en la toolbar
            if hasattr(self._main_window, "toolbar"):
                self._main_window.toolbar.actualizar_estado_conexion(conectado=False)
        else:
            _LOG.debug("Estado de socket: %s", state)

    def desconectar(self) -> None:
        """Desconecta el cliente del servidor."""
        if self._socket.state() == QAbstractSocket.SocketState.ConnectedState:
            self._socket.disconnectFromHost()
            _LOG.info("Solicitando desconexión del servidor")

    def display_error(self) -> None:
        """Maneja y muestra errores de conexión."""
        err = self._socket.errorString()
        if err == "Connection refused":
            QMessageBox.warning(
                self,
                _("Advertencia"),
                _("Conexión rechazada por el servidor."),
            )
        _LOG.warning("Error de socket: %s", err)
