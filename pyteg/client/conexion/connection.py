"""Módulo para manejar la conexión del cliente al servidor."""

from __future__ import annotations

import json
import uuid
from typing import Any

from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import QMessageBox, QWidget

from pyteg.client.conexion.transmisor import ClientNullTransmisor, ClientTransmisor
from pyteg.client.event_processor import ClientEventProcessor
from pyteg.client.hosting import HostSession
from pyteg.client.secure_transport import tls_socket, verify_socket
from pyteg.client.state_adapter import QtClientStateAdapter
from pyteg.client.state_model import ClientStateModel
from pyteg.client.tasks.manager import ClientTaskManager
from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.config import DEFAULT_MAP_THEME
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.network.game_security import signed_command
from pyteg.network.security import SECURITY_VERSION, Invitation, proof
from pyteg.protocol import PROTOCOL_VERSION, map_hash_for_theme
from pyteg.protocol_validation import MessageValidationError, validate_client_event

_LOG = get_logger("client.connection")


class ConnectionClient(QWidget):
    """Widget que maneja la conexión TCP del cliente al servidor."""

    def __init__(
        self,
        main_window: Any,
        host: str = "127.0.0.1",
        port: int = 65432,
        username: str = "Usuario",
        *,
        invitation: Invitation | str | None = None,
    ) -> None:
        """Inicializa la conexión del cliente.

        Args:
            main_window: Ventana principal de la aplicación.
            host: Dirección IP del servidor.
            port: Puerto del servidor.
            username: Nombre de usuario del cliente.
            invitation: Enlace que autoriza el ingreso y fija la identidad remota.

        """
        super().__init__(main_window if isinstance(main_window, QWidget) else None)
        self._host = host
        self._port = port
        self._username = username
        self._main_window = main_window
        self.state_model = ClientStateModel()
        self.event_processor = ClientEventProcessor(self.state_model)
        self.state_adapter = QtClientStateAdapter(main_window, self.state_model)
        main_window.client_state_model = self.state_model
        self._socket = tls_socket(self)
        self.invitation = (
            Invitation.parse(invitation) if isinstance(invitation, str) else invitation
        )
        self.remote_key = (
            self.invitation.public_key if self.invitation is not None else ""
        )
        self._security_ready = False
        self._security_nonce = ""
        self._security_sequence = 0
        self._codec = NulDelimitedUtf8Codec()
        self._socket.readyRead.connect(self.read_data)
        self._socket.errorOccurred.connect(self.display_error)
        self._socket.stateChanged.connect(self.on_state_changed)
        self._socket.encrypted.connect(self._encrypted)
        self.hosting = HostSession(self, main_window)

    def conectar(self) -> None:
        """Establece la conexión con el servidor.

        Raises:
            ValueError: Si falta una invitación válida para este destino.

        """
        if self.invitation is None:
            self.invitation = self.hosting.runtime().invitation(self._host)
            self.remote_key = self.invitation.public_key
        if self.invitation.mode != "host":
            msg = "La invitación corresponde a otro tipo de red"
            raise ValueError(msg)
        self._security_ready = False
        self._security_nonce = ""
        self._security_sequence = 0
        self._socket.connectToHostEncrypted(self._host, self._port)
        _LOG.info("Conectando a %s:%s...", self._host, self._port)

    def _encrypted(self) -> None:
        try:
            verify_socket(self._socket, self.remote_key)
            self._codec = NulDelimitedUtf8Codec()
        except (ValueError, TypeError) as error:
            self._main_window.update_status_bar(str(error))
            self._socket.abort()

    def _security_event(self, event: object) -> bool:
        if self._security_ready:
            return False
        if not isinstance(event, dict):
            msg = "El mensaje de red debe ser un objeto"
            raise TypeError(msg)
        invitation = self.invitation
        if invitation is None or event.get("security") != SECURITY_VERSION:
            msg = "El destino no admite una conexión segura a esta sala"
            raise ValueError(msg)
        verify_socket(self._socket, self.remote_key)
        if "nonce" in event:
            self._security_nonce = event["nonce"]
            request = {
                "message": "connect",
                "session_id": invitation.session_id,
                "invite": invitation.token,
                "user_id": self._main_window.client.userid(),
            }
            packet = proof(self.hosting.runtime().identity, event, request)
            self._socket.write(NulDelimitedUtf8Codec.encode_frame(json.dumps(packet)))
        elif event.get("accepted") is True and self._security_nonce:
            self._security_ready = True
            self.on_connected()
        else:
            msg = "La sala rechazó la prueba de identidad"
            raise ValueError(msg)
        return True

    def on_connected(self) -> None:
        """Maneja el evento de conexión exitosa al servidor."""
        _LOG.info("Conectado a %s:%s", self._host, self._port)
        self._main_window.conexion = self
        self._main_window.transmisor = ClientTransmisor(self)
        if self._main_window.ventana_conectar is not None:
            self._main_window.ventana_conectar.close()
        if hasattr(self._main_window, "toolbar"):
            self._main_window.toolbar.actualizar_estado_conexion(conectado=True)
        self.hosting.connected()
        # Reproducir sonido de conexión
        if hasattr(self._main_window, "sound_manager"):
            self._main_window.sound_manager.play_connect()
        # Actualizar estado en la interfaz
        self._main_window.update_game_state("Conectado")
        # Usar el transmisor de main_window
        user_id = self._main_window.client.userid()
        token_getter = getattr(self._main_window.client, "reconnect_token", None)
        token = token_getter() if callable(token_getter) else None
        # El servidor envía el hash en su anuncio ``hello``; para la conexión
        # Qt local usamos el mismo cálculo canónico del tema configurado.
        theme = getattr(
            self._main_window,
            "map_theme",
            getattr(self._main_window, "theme", DEFAULT_MAP_THEME),
        )
        if not isinstance(theme, str) or not theme:
            theme = DEFAULT_MAP_THEME
        try:
            map_hash = map_hash_for_theme(theme)
        except OSError:
            map_hash = "client-map-unknown"
        self._main_window.transmisor.hello(
            PROTOCOL_VERSION,
            theme,
            map_hash,
            capabilities=[
                "snapshots",
                "command_results",
                "reconnect",
                "heartbeat",
                "host_migration",
            ],
            rules=["validated_phases", "one_card_per_turn"],
        )
        if user_id is not None and token:
            self._main_window.transmisor.reconectar(user_id, token)
        else:
            self._main_window.transmisor.set_username(self._username)

    def esta_conectado(self) -> bool:
        """Verifica si el cliente está conectado al servidor.

        Returns:
            True si está conectado, False en caso contrario.

        """
        connected = (
            self._security_ready
            and self._socket.isEncrypted()
            and self._socket.state() == QAbstractSocket.SocketState.ConnectedState
        )
        _LOG.debug("Socket state=%s connected=%s", self._socket.state(), connected)
        return connected

    def endpoint(self) -> tuple[str, int]:
        """Devuelve el destino activo de esta conexión.

        Returns:
            Dirección y puerto del anfitrión actual.

        """
        return self._host, self._port

    def reconnect_to(
        self, host: str, port: int, *, public_key: str | None = None
    ) -> None:
        """Reutiliza el socket Qt para recuperar la sesión en otro destino."""
        self._host, self._port = host, port
        if public_key is not None:
            self.remote_key = public_key
        self.conectar()

    def abort_for_recovery(self) -> None:
        """Interrumpe el intento actual sin marcar una salida voluntaria."""
        self._socket.abort()

    def reset_replica_revision(self) -> None:
        """Acepta la revisión restaurada de una nueva autoridad de la sala."""
        self.state_model.revision = -1

    def esta_ocupada(self) -> bool:
        """Indica si este objeto ya tiene una conexión abierta o en curso.

        ``esta_conectado`` sólo informa el estado establecido; el diálogo de
        conexión también debe bloquear un segundo intento mientras Qt todavía
        resuelve el host o negocia el socket.

        Returns:
            ``True`` si el socket está conectado o en proceso de conexión.

        """
        return self._socket.state() != QAbstractSocket.SocketState.UnconnectedState

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
        if not self._security_ready or self.invitation is None:
            return
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and payload.get("mensaje") != "hello":
            payload.setdefault("command_id", uuid.uuid4().hex)
        if not isinstance(payload, dict):
            return
        self._security_sequence += 1
        packet = signed_command(
            self.hosting.runtime().identity,
            self.invitation.session_id,
            self._security_nonce,
            self._security_sequence,
            payload,
        )
        data = json.dumps(packet, ensure_ascii=False)
        _LOG.debug("Enviando mensaje (%s bytes)", len(data))
        encode_data = NulDelimitedUtf8Codec.encode_frame(data)
        self._socket.write(encode_data)

    def read_data(self) -> None:  # noqa: C901, PLR0912 -- framing, seguridad y proyección de eventos.
        """Lee datos recibidos del servidor."""
        while self._socket.bytesAvailable():
            encode_datas = self._socket.readAll()
            encoded_chunk = bytes(encode_datas)
            try:
                datas = self._codec.feed(encoded_chunk)
            except FrameCodecError as error:
                _LOG.warning("Trama TCP inválida recibida del servidor: %s", error)
                self._socket.disconnectFromHost()
                return
            _LOG.debug(
                "Recibido chunk (%s bytes); %s trama(s) completa(s), %s pendiente(s)",
                len(encoded_chunk),
                len(datas),
                self._codec.pending_bytes,
            )
            for data in datas:
                if not data:
                    continue
                _LOG.debug("Fragmento recibido (%s bytes)", len(data))
                try:
                    data_json = json.loads(data)
                except json.JSONDecodeError:
                    _LOG.warning("Mensaje no JSON del servidor: %s", data[:200])
                    continue

                try:
                    if self._security_event(data_json):
                        continue
                except (ValueError, TypeError, KeyError) as error:
                    self._main_window.update_status_bar(str(error))
                    self._socket.abort()
                    return

                try:
                    validated_data = validate_client_event(data_json)
                except MessageValidationError as error:
                    _LOG.warning("Evento inválido del servidor: %s", error)
                    continue

                _LOG.debug("JSON recibido: %s", validated_data["mensaje"])
                if self.hosting.process(validated_data):
                    continue
                if self._respond_to_ping(validated_data):
                    continue
                applied = self.event_processor.process(validated_data)
                if applied.gap:
                    self.send_data(
                        json.dumps({
                            "mensaje": "solicitar_snapshot",
                            "command_id": uuid.uuid4().hex,
                        })
                    )
                self.state_adapter.apply(validated_data, applied)
                if self.state_adapter.handles(validated_data.get("mensaje")):
                    continue
                try:
                    task = ClientTaskManager.msg_to_task(validated_data)
                    task.run(self._main_window)
                except Exception:  # noqa: BLE001 - el slot Qt no debe caer por un peer.
                    _LOG.exception("Error al procesar evento del servidor")

    def _respond_to_ping(self, event: dict[str, Any]) -> bool:
        """Responde un heartbeat sin proyectarlo como evento de juego.

        Returns:
            ``True`` si el evento era un ping y se respondió.

        """
        if event.get("mensaje") != "ping":
            return False
        self.send_data(
            json.dumps({
                "mensaje": "pong",
                "heartbeat_id": event["heartbeat_id"],
            })
        )
        return True

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
            _LOG.info("Negociando identidad y cifrado del socket")
        elif state == QAbstractSocket.SocketState.UnconnectedState:
            self._security_ready = False
            _LOG.info("Socket desconectado")
            self._main_window.conexion = None
            self._main_window.transmisor = ClientNullTransmisor()
            # Reproducir sonido de desconexión
            if hasattr(self._main_window, "sound_manager"):
                self._main_window.sound_manager.play_disconnect()
            self._main_window.update_game_state("Desconectado")
            # Actualizar estado de botones en la toolbar
            if hasattr(self._main_window, "toolbar"):
                self._main_window.toolbar.actualizar_estado_conexion(conectado=False)
            if self.hosting.disconnected():
                self._main_window.conexion = self
                self._main_window.update_game_state("Recuperando partida")
        else:
            _LOG.debug("Estado de socket: %s", state)

    def desconectar(self) -> None:
        """Desconecta el cliente del servidor."""
        self.hosting.stop()
        if self._socket.state() == QAbstractSocket.SocketState.ConnectedState:
            self._socket.disconnectFromHost()
            _LOG.info("Solicitando desconexión del servidor")

    def abortar(self) -> None:
        """Cierra enseguida una conexión cuya negociación fue rechazada."""
        self._socket.abort()

    def display_error(self) -> None:
        """Maneja y muestra errores de conexión."""
        err = self._socket.errorString()
        if hasattr(self._main_window, "sound_manager"):
            self._main_window.sound_manager.play_error()
        if err == "Connection refused" and not self.hosting.enabled:
            QMessageBox.warning(
                self,
                _("Advertencia"),
                _("Conexión rechazada por el servidor."),
            )
        _LOG.warning("Error de socket: %s", err)
