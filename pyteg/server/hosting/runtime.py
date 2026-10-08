"""Servicio de anfitrión integrado, con puerto de recuperación autenticado."""

from __future__ import annotations

import json
import secrets
import socket
import threading
import time
from copy import deepcopy
from typing import Any

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.logger import get_logger
from pyteg.server.app import Server
from pyteg.server.conexion.registrar_jugadores import PlayerListener
from pyteg.server.hosting.checkpoint import CHECKPOINT_VERSION, restore_checkpoint
from pyteg.server.hosting.replication import HostReplication
from pyteg.server.hosting.sessions import finish_migration

_LOG = get_logger(__name__)
MIGRATION_GRACE_SECONDS = 8.0
_CONTROL_LIMIT = 4096
_PEER_STATUS_TIMEOUT = 0.2
_MAX_PORT = 65535


class HostRuntime:
    """Mantiene un único motor activo y una copia inerte mientras es suplente."""

    def __init__(self, *, bind_host: str = "0.0.0.0") -> None:  # noqa: S104 -- red local.
        """Abre un puerto efímero de recuperación; todavía no crea una partida.

        Raises:
            OSError: Si no se puede reservar o utilizar el puerto TCP.

        """
        self._bind_host = bind_host
        self._lock = threading.RLock()
        self._checkpoint: dict[str, Any] | None = None
        self._user_id: int | None = None
        self._primary: tuple[str, int] | None = None
        self._server: Server | None = None
        self._listener: PlayerListener | None = None
        self._grace: threading.Timer | None = None
        self._stop = threading.Event()
        self._slots = threading.BoundedSemaphore(8)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.bind((bind_host, 0))
            self._socket.listen(8)
            self._socket.settimeout(0.2)
        except OSError:
            self._socket.close()
            raise
        self.control_port = int(self._socket.getsockname()[1])
        self._thread = threading.Thread(
            target=self._accept, name="pyteg-host-recovery", daemon=True
        )
        self._thread.start()

    @property
    def server(self) -> Server | None:
        """Devuelve el motor sólo cuando esta instancia es anfitriona."""
        return self._server

    def create_game(
        self, theme: str, port: int, *, rules_profile: str | None = None
    ) -> int:
        """Crea una sala y reserva su puerto antes de conectar el cliente local.

        Returns:
            Puerto TCP reservado para los jugadores.

        Raises:
            OSError: Si no se puede reservar o utilizar el puerto TCP.
            ValueError: Si los datos no son compatibles o la sesión no es válida.

        """
        with self._lock:
            if self._stop.is_set():
                msg = "El servicio de anfitrión está cerrado"
                raise ValueError(msg)
            if self._server is not None:
                msg = "Esta instancia ya hospeda una partida"
                raise ValueError(msg)
            server = Server(theme, rules_profile=rules_profile)
            try:
                listener = PlayerListener(server, self._bind_host, port)
            except OSError:
                server.detener()
                raise
            server.host_replication = HostReplication(server, self.store_checkpoint)
            self._server, self._listener = server, listener
            listener.start()
            return listener.port

    def store_checkpoint(
        self, envelope: dict[str, Any], *, user_id: int | None = None
    ) -> bool:
        """Conserva sólo copias completas y más recientes de la misma sala.

        Returns:
            True si se conservó una copia más reciente.

        """
        checkpoint = envelope.get("checkpoint")
        if (
            not isinstance(checkpoint, dict)
            or checkpoint.get("version") != CHECKPOINT_VERSION
        ):
            return False
        with self._lock:
            if self._stop.is_set():
                return False
            if user_id is not None:
                self._user_id = user_id
            current = self._checkpoint
            if current is not None:
                if current["session_id"] != envelope["session_id"]:
                    return False
                if (envelope["epoch"], envelope["sequence"]) <= (
                    current["epoch"],
                    current["sequence"],
                ):
                    return False
            self._checkpoint = deepcopy(envelope)
            return True

    def latest_checkpoint(self) -> dict[str, Any] | None:
        """Devuelve una copia del último punto completo de recuperación.

        Returns:
            Última copia completa o None si todavía no se recibió una.

        """
        with self._lock:
            return deepcopy(self._checkpoint)

    def primary_connection(self, endpoint: tuple[str, int] | None) -> None:
        """Impide promover un suplente que todavía ve al anfitrión activo."""
        with self._lock:
            self._primary = endpoint

    def recover(self, request: dict[str, Any]) -> dict[str, Any]:
        """Autoriza una promoción con el token de un jugador de la sala.

        Returns:
            Destino del anfitrión vigente o del nuevo anfitrión recuperado.

        Raises:
            ValueError: Si los datos no son compatibles o la sesión no es válida.

        """
        with self._lock:
            envelope = self._authenticate(request)
            if self._server is None and self._primary is not None:
                return {
                    "mensaje": "host_alive",
                    "session_id": envelope["session_id"],
                    "epoch": envelope["epoch"],
                    "host": self._primary[0],
                    "port": self._primary[1],
                }
            if self._server is None:
                authority = self._find_live_authority(envelope, request)
                if authority is not None:
                    return authority
                self._promote(envelope)
            if (
                self._listener is None
                or self._server is None
                or self._server.host_replication is None
            ):
                msg = "El anfitrión no pudo iniciarse"
                raise ValueError(msg)
            replication = self._server.host_replication
            return {
                "mensaje": "host_ready",
                "session_id": replication.session_id,
                "epoch": replication.epoch,
                "port": self._listener.port,
                "owner_id": replication.owner_id,
            }

    def _authenticate(self, request: dict[str, Any]) -> dict[str, Any]:
        envelope = self._checkpoint
        if self._stop.is_set():
            msg = "El servicio de anfitrión está cerrado"
            raise ValueError(msg)
        if envelope is None or request.get("session_id") != envelope["session_id"]:
            msg = "No existe una copia de esa sala"
            raise ValueError(msg)
        player = next(
            (
                player
                for player in envelope["checkpoint"]["players"]
                if player["userid"] == request.get("user_id")
            ),
            None,
        )
        token = request.get("token")
        if (
            player is None
            or not isinstance(token, str)
            or not secrets.compare_digest(player["token"], token)
        ):
            msg = "La recuperación requiere una sesión válida"
            raise ValueError(msg)
        epoch = request.get("epoch")
        if (
            not isinstance(epoch, int)
            or isinstance(epoch, bool)
            or epoch < 0
            or epoch not in {envelope["epoch"], envelope["epoch"] - 1}
        ):
            msg = "La época de recuperación ya no está vigente"
            raise ValueError(msg)
        return envelope

    def status(self, request: dict[str, Any]) -> dict[str, Any]:
        """Consulta autenticada que nunca promueve un motor.

        No toma el bloqueo de promoción: dos candidatos pueden consultar su
        estado entre sí mientras deciden si todavía existe un anfitrión.

        Returns:
            Estado del anfitrión conocido por este participante.

        """
        envelope = self._authenticate(request)
        server, listener, primary = self._server, self._listener, self._primary
        response = {
            "mensaje": "host_standby",
            "session_id": envelope["session_id"],
            "epoch": envelope["epoch"],
        }
        if server is not None and listener is not None:
            replication = server.host_replication
            if replication is not None:
                response.update(
                    mensaje="host_ready",
                    epoch=replication.epoch,
                    port=listener.port,
                    owner_id=replication.owner_id,
                )
        elif primary is not None:
            response.update(mensaje="host_alive", host=primary[0], port=primary[1])
        return response

    def _find_live_authority(
        self, envelope: dict[str, Any], request: dict[str, Any]
    ) -> dict[str, Any] | None:
        for peer in envelope["peers"]:
            if peer["userid"] == self._user_id:
                continue
            try:
                response = self._query_peer(peer, {**request, "mensaje": "host_status"})
            except OSError, ValueError, FrameCodecError:
                continue
            port = response.get("port")
            if (
                response.get("session_id") != envelope["session_id"]
                or not isinstance(port, int)
                or isinstance(port, bool)
                or not 1 <= port <= _MAX_PORT
            ):
                continue
            if response.get("mensaje") == "host_ready":
                response["host"] = peer["host"]
                if response.get("epoch") == envelope["epoch"]:
                    response["mensaje"] = "host_alive"
                elif response.get("epoch") != envelope["epoch"] + 1:
                    continue
                return response
            if (
                response.get("mensaje") == "host_alive"
                and response.get("epoch") == envelope["epoch"]
                and isinstance(response.get("host"), str)
                and response["host"]
            ):
                return response
        return None

    @staticmethod
    def _query_peer(peer: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        deadline = time.monotonic() + _PEER_STATUS_TIMEOUT
        with socket.create_connection(
            (peer["host"], peer["port"]), timeout=_PEER_STATUS_TIMEOUT
        ) as conn:
            conn.sendall(NulDelimitedUtf8Codec.encode_frame(json.dumps(request)))
            codec = NulDelimitedUtf8Codec(_CONTROL_LIMIT)
            while time.monotonic() < deadline:
                conn.settimeout(max(0.01, deadline - time.monotonic()))
                data = conn.recv(_CONTROL_LIMIT)
                if not data:
                    break
                frames = codec.feed(data)
                if frames:
                    response = json.loads(frames[0])
                    if isinstance(response, dict):
                        return response
                    break
        return {}

    def _promote(self, envelope: dict[str, Any]) -> None:
        checkpoint = envelope["checkpoint"]
        own_peer = next(
            (peer for peer in envelope["peers"] if peer["userid"] == self._user_id),
            None,
        )
        if own_peer is None:
            msg = "Este participante no está registrado como candidato"
            raise ValueError(msg)
        server = Server(checkpoint["theme"])
        try:
            server.migration_sessions = restore_checkpoint(server, checkpoint)
            server.host_migrating = True
            server.host_resume_seconds = checkpoint["remaining"]
            listener = PlayerListener(
                server,
                self._bind_host,
                0,
                first_user_id=max(server.migration_sessions, default=0) + 1,
            )
        except Exception:
            server.detener()
            raise
        peers = [
            peer for peer in envelope["peers"] if peer["userid"] != envelope["owner_id"]
        ]
        server.host_replication = HostReplication(
            server,
            self.store_checkpoint,
            session_id=envelope["session_id"],
            epoch=envelope["epoch"] + 1,
            owner_id=own_peer["userid"],
            sequence=envelope["sequence"],
            peers=peers,
        )
        self._server, self._listener = server, listener
        listener.start()
        self._grace = threading.Timer(
            MIGRATION_GRACE_SECONDS,
            lambda: server.schedule_host_recovery(
                lambda: finish_migration(server, checkpoint["remaining"])
            ),
        )
        self._grace.daemon = True
        self._grace.start()

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _addr = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            if not self._slots.acquire(blocking=False):
                conn.close()
                continue
            threading.Thread(target=self._control, args=(conn,), daemon=True).start()

    def _control(self, conn: socket.socket) -> None:
        try:
            conn.settimeout(2.0)
            codec = NulDelimitedUtf8Codec(_CONTROL_LIMIT)
            frames: list[str] = []
            deadline = time.monotonic() + 2.0
            while not frames:
                conn.settimeout(max(0.01, deadline - time.monotonic()))
                if time.monotonic() >= deadline:
                    return
                data = conn.recv(_CONTROL_LIMIT)
                if not data:
                    return
                frames = codec.feed(data)
            request = json.loads(frames[0])
            if not isinstance(request, dict) or request.get("mensaje") not in {
                "recover_host",
                "host_status",
            }:
                return
            response = (
                self.status(request)
                if request["mensaje"] == "host_status"
                else self.recover(request)
            )
            conn.sendall(NulDelimitedUtf8Codec.encode_frame(json.dumps(response)))
        except (OSError, ValueError, KeyError, TypeError, FrameCodecError) as error:
            _LOG.debug("Solicitud de recuperación rechazada: %s", error)
        finally:
            conn.close()
            self._slots.release()

    def close(self) -> None:
        """Cierra listeners, temporizador y sockets al salir del cliente."""
        self._stop.set()
        self._socket.close()
        with self._lock:
            server, listener, grace = self._server, self._listener, self._grace
            self._server = None
            self._listener = None
        if grace is not None:
            grace.cancel()
        if listener is not None:
            listener.close()
        if server is not None:
            server.host_replication = None
            server.detener()
            for client in server.dame_clientes():
                client.cerrar()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=1.0)
