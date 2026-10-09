"""Coordinación Qt del anfitrión y recuperación automática de la conexión."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QAbstractSocket, QNetworkInterface, QTcpSocket

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.server.hosting.runtime import HostRuntime

if TYPE_CHECKING:
    from pyteg.client.conexion.connection import ConnectionClient

_LOG = get_logger(__name__)
_TCP_MAX_PORT = 65535
_PROBE_TIMEOUT_MS = 2000
_HOST_SILENCE_SECONDS = 6.0


def local_game_addresses() -> list[str]:
    """Devuelve direcciones IPv4 locales que pueden compartir los jugadores.

    Returns:
        Direcciones de las interfaces locales o loopback si no hay otra.

    """
    return sorted({
        address.toString()
        for address in QNetworkInterface.allAddresses()
        if address.protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol
        and not address.isLoopback()
    }) or ["127.0.0.1"]


def _recovery_destination(
    response: object, envelope: dict[str, Any], target: dict[str, Any]
) -> tuple[str, int, bool] | None:
    if not isinstance(response, dict):
        return None
    port, epoch = response.get("port"), response.get("epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool):
        return None
    if (
        not isinstance(port, int)
        or isinstance(port, bool)
        or not 1 <= port <= _TCP_MAX_PORT
        or response.get("session_id") != envelope["session_id"]
    ):
        return None
    if response.get("mensaje") == "host_ready" and epoch > envelope["epoch"]:
        host = response.get("host", target["host"])
        promoted = True
    elif response.get("mensaje") == "host_alive" and epoch >= envelope["epoch"]:
        host = response.get("host")
        promoted = epoch > envelope["epoch"]
    else:
        return None
    if not isinstance(host, str) or not host:
        return None
    return host, port, promoted


class HostSession(QObject):
    """Gestiona reintentos y candidatos; el motor permanece fuera de la GUI."""

    def __init__(self, connection: ConnectionClient, window: Any) -> None:
        """Prepara supervisión sin iniciar servidores para conexiones antiguas."""
        super().__init__(connection)
        self.connection = connection
        self.window = window
        self.enabled = False
        self.recovering = False
        self.paused = False
        self._intentional = False
        self._last_received = time.monotonic()
        self._quorum_since: float | None = None
        self._saved_id: int | None = None
        self._saved_token: str | None = None
        self._peers: list[dict[str, Any]] = []
        self._envelope: dict[str, Any] | None = None
        self._probe: QTcpSocket | None = None
        self._probe_codec = NulDelimitedUtf8Codec(4096)
        self._target: dict[str, Any] | None = None
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(self._next_candidate)
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(1000)
        self._watchdog.timeout.connect(self._check_silence)

    def runtime(self) -> HostRuntime:
        """Obtiene el servicio compartido con la ventana de creación de partida.

        Returns:
            Servicio de anfitrión de esta ventana.

        """
        runtime = getattr(self.window, "host_runtime", None)
        if not isinstance(runtime, HostRuntime):
            files = getattr(self.window, "files_manager", None)
            repository = files.network_repository() if files is not None else None
            runtime = HostRuntime(repository=repository)
            self.window.host_runtime = runtime
        return runtime

    def connected(self) -> None:
        """Muestra la conexión también al usar el servidor independiente."""
        host, port = self.connection.endpoint()
        self._show_status(f"{_('Conectado')} · {host}:{port}")

    def process(self, event: dict[str, Any]) -> bool:
        """Procesa negociación y copias sin enviarlas al modelo público del mapa.

        Returns:
            True si el evento pertenece a la recuperación y ya fue procesado.

        """
        self._last_received = time.monotonic()
        kind = event["mensaje"]
        if kind != "host_checkpoint":
            return self._process_control(event)
        if not self.enabled:
            return True
        user_id = self.window.client.userid()
        previous = self._envelope
        if previous is not None and (
            event["session_id"] != previous["session_id"]
            or (event["epoch"], event["sequence"])
            <= (previous["epoch"], previous["sequence"])
        ):
            return True
        runtime = self.runtime()
        runtime.store_checkpoint(event, user_id=user_id)
        if not runtime.can_follow(event):
            return True
        # El anfitrión ya guardó esta copia al publicarla. La proyección Qt
        # tiene su propia revisión y también necesita recibirla.
        if event["checkpoint"]["version"] == 1:
            self._envelope = event
            self._quorum_since = None
            was_paused = self.paused
            self.paused = event.get("recovering") is True
            self.runtime().primary_connection(self.connection.endpoint())
            owner = event["owner_id"]
            role = _("Anfitrión") if owner == user_id else _("Conectado")
            if self.paused:
                role = _("Recuperando partida…")
            self._show_status(
                f"{role} · "
                f"{self.connection.endpoint()[0]}:{self.connection.endpoint()[1]}"
            )
            if was_paused != self.paused:
                self.window.refresh_gameplay_actions()
        return True

    def _process_control(self, event: dict[str, Any]) -> bool:
        kind = event["mensaje"]
        if kind == "host_room":
            self.runtime().join_room(event["session_id"])
            return True
        if kind == "hello" and "host_migration" in event.get("capabilities", []):
            self.enabled = True
            self.runtime()
            self.runtime().primary_connection(self.connection.endpoint())
            self._watchdog.start()
        if self.enabled and kind == "hello_ack" and event.get("accepted"):
            self.runtime().set_identity(self.window.client.userid())
            self.connection.send_data(
                json.dumps({
                    "mensaje": "host_candidate",
                    "port": self.runtime().control_port,
                })
            )
        if kind == "reconexion" and self.recovering:
            self.recovering = False
            self._quorum_since = None
            self._deadline.stop()
            self.runtime().primary_connection(self.connection.endpoint())
            self._show_status("Partida recuperada")
        if self.enabled and kind == "reconexion":
            self.runtime().set_identity(self.window.client.userid())
            self.connection.send_data(
                json.dumps({
                    "mensaje": "host_candidate",
                    "port": self.runtime().control_port,
                })
            )
        if kind == "host_availability":
            self.paused = event["paused"]
            self._quorum_since = (
                (self._quorum_since or time.monotonic()) if self.paused else None
            )
            if self.paused:
                self._show_status(_("Esperando copias de seguridad…"))
            self.window.refresh_gameplay_actions()
            return True
        return False

    def disconnected(self) -> bool:
        """Recupera sólo caídas inesperadas que ya tengan una copia completa.

        Returns:
            True si comenzó o continúa la recuperación automática.

        """
        runtime = getattr(self.window, "host_runtime", None)
        if isinstance(runtime, HostRuntime):
            runtime.primary_connection(None)
        if self._intentional or not self.enabled or self._envelope is None:
            self._show_status("Desconectado")
            return False
        if self.recovering:
            return True
        self._saved_id = self.window.client.userid()
        self._saved_token = self.window.client.reconnect_token()
        if self._saved_id is None or not self._saved_token:
            return False
        self.recovering = True
        self.paused = True
        self._peers = [
            peer
            for peer in self._envelope["peers"]
            if peer["userid"] != self._envelope["owner_id"]
        ]
        self._show_status("Recuperando partida…")
        self._deadline.start(_PROBE_TIMEOUT_MS)
        QTimer.singleShot(100, self, self._retry_primary)
        return True

    def _retry_primary(self) -> None:
        if self.recovering:
            self._restore_identity()
            self.connection.reconnect_to(*self.connection.endpoint())

    def _restore_identity(self) -> None:
        if self._saved_id is not None and self._saved_token is not None:
            self.window.client.set_userid(self._saved_id)
            self.window.client.set_reconnect_token(self._saved_token)

    def _next_candidate(self) -> None:
        if not self.recovering:
            return
        self._close_probe()
        self.connection.abort_for_recovery()
        if not self._peers:
            if self._envelope is not None and self._envelope.get("durable"):
                self._peers = [
                    peer
                    for peer in self._envelope["peers"]
                    if peer["userid"] != self._envelope["owner_id"]
                ]
                self._show_status(_("Esperando una mayoría de jugadores…"))
                self._deadline.start(_PROBE_TIMEOUT_MS)
                return
            self.recovering = False
            self.window.update_game_state("Desconectado")
            self._show_status("No hay un anfitrión disponible")
            return
        self._target = self._peers.pop(0)
        probe = QTcpSocket(self)
        self._probe = probe
        self._probe_codec = NulDelimitedUtf8Codec(4096)
        probe.connected.connect(self._send_recovery_request)
        probe.readyRead.connect(self._read_recovery_response)
        probe.errorOccurred.connect(
            lambda error, probe=probe: self._probe_error(probe, error)
        )
        probe.connectToHost(self._target["host"], self._target["port"])
        self._deadline.start(_PROBE_TIMEOUT_MS)

    def _send_recovery_request(self) -> None:
        if self._probe is None or self._envelope is None:
            return
        request = {
            "mensaje": "recover_host",
            "session_id": self._envelope["session_id"],
            "epoch": self._envelope["epoch"],
            "user_id": self._saved_id,
            "token": self._saved_token,
        }
        self._probe.write(NulDelimitedUtf8Codec.encode_frame(json.dumps(request)))

    def _read_recovery_response(self) -> None:
        if self._probe is None or self._envelope is None or self._target is None:
            return
        try:
            responses = self._probe_codec.feed(bytes(self._probe.readAll()))
            if not responses:
                return
            response = json.loads(responses[0])
            destination = _recovery_destination(response, self._envelope, self._target)
            if destination is None:
                self._next_candidate()
                return
            host, port, promoted = destination
            if promoted:
                self.connection.reset_replica_revision()
            self._close_probe()
            self._restore_identity()
            self.connection.reconnect_to(host, port)
            self._deadline.start(_PROBE_TIMEOUT_MS)
        except (ValueError, TypeError, KeyError, FrameCodecError) as error:
            _LOG.warning("Respuesta de recuperación inválida: %s", error)
            self._next_candidate()

    def _probe_error(
        self, probe: QTcpSocket, _error: QAbstractSocket.SocketError
    ) -> None:
        if self.recovering and probe is self._probe:
            QTimer.singleShot(
                0,
                self,
                lambda: self._next_candidate() if probe is self._probe else None,
            )

    def _close_probe(self) -> None:
        probe, self._probe = self._probe, None
        if probe is not None:
            probe.blockSignals(True)  # noqa: FBT003 -- API Qt.
            probe.abort()
            probe.deleteLater()

    def _check_silence(self) -> None:
        now = time.monotonic()
        quorum_stalled = (
            self._quorum_since is not None
            and now - self._quorum_since > _HOST_SILENCE_SECONDS
        )
        if (
            self.enabled
            and not self.recovering
            and self.connection.esta_conectado()
            and (now - self._last_received > _HOST_SILENCE_SECONDS or quorum_stalled)
        ):
            self.connection.abort_for_recovery()

    def _show_status(self, text: str) -> None:
        text = _(text)
        self.window.network_status = text
        label = getattr(self.window, "network_status_label", None)
        if label is not None:
            label.setText(text.split(" · ", 1)[0])
            runtime = getattr(self.window, "host_runtime", None)
            if isinstance(runtime, HostRuntime) and runtime.server is not None:
                port = self.connection.endpoint()[1]
                text += "\n" + _("Direcciones para unirse: {}").format(
                    ", ".join(f"{host}:{port}" for host in local_game_addresses())
                )
            label.setToolTip(text)

    def stop(self) -> None:
        """Cancela reintentos cuando el usuario sale o se desconecta."""
        self._intentional = True
        self.recovering = False
        self.paused = False
        self._watchdog.stop()
        self._deadline.stop()
        self._close_probe()
        runtime = getattr(self.window, "host_runtime", None)
        if isinstance(runtime, HostRuntime):
            runtime.close()
            self.window.host_runtime = None
        self._show_status("Desconectado")
