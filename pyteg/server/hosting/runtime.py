"""Servicio de anfitrión integrado, con puerto de recuperación autenticado."""

from __future__ import annotations

import json
import secrets
import socket
import threading
import time
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from pyteg.codecs_utils import (
    DEFAULT_MAX_FRAME_BYTES,
    FrameCodecError,
    NulDelimitedUtf8Codec,
)
from pyteg.logger import get_logger
from pyteg.network.discovery import RoomAnnouncer
from pyteg.persistence.archive import (
    ArchiveRepository,
    MemoryRepository,
    digest,
    make_archive,
    read_archive,
    write_archive,
)
from pyteg.persistence.wire import decode_envelope, encode_envelope
from pyteg.protocol import PROTOCOL_VERSION
from pyteg.protocol_validation import validate_client_event
from pyteg.server.conexion.registrar_jugadores import PlayerListener
from pyteg.server.hosting.checkpoint import CHECKPOINT_VERSION
from pyteg.server.hosting.consensus import ElectionState, joint_majority, majority
from pyteg.server.hosting.engine import RecoveryEngine, ServerEngine
from pyteg.server.hosting.replication import HostReplication

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from pyteg.server.app import Server

_LOG = get_logger(__name__)
MIGRATION_GRACE_SECONDS = 8.0
_CONTROL_LIMIT = DEFAULT_MAX_FRAME_BYTES
_PEER_STATUS_TIMEOUT = 1.0
_BACKUP_TIMEOUT = 1.0
_MAX_PORT = 65535


class HostRuntime:
    """Mantiene un único motor activo y una copia inerte mientras es suplente."""

    def __init__(
        self,
        *,
        bind_host: str = "0.0.0.0",  # noqa: S104 -- sala de red local.
        repository: ArchiveRepository | None = None,
        engine: RecoveryEngine | None = None,
    ) -> None:
        """Abre un puerto efímero de recuperación; todavía no crea una partida.

        Raises:
            OSError: Si no se puede reservar o utilizar el puerto TCP.

        """
        self._bind_host = bind_host
        self._repository = repository or MemoryRepository()
        self._engine = engine or ServerEngine()
        self._lock = threading.RLock()
        self._backup_lock = threading.RLock()
        self._election = ElectionState()
        self._pending: dict[str, Any] | None = None
        self._announcer: RoomAnnouncer | None = None
        self._checkpoint: dict[str, Any] | None = None
        self._user_id: int | None = None
        self._primary: tuple[str, int] | None = None
        self._primary_epoch: int | None = None
        self._session_id = ""
        self._server: Server | None = None
        self._listener: PlayerListener | None = None
        self._grace: threading.Timer | None = None
        self.restored_waiting = False
        self._stop = threading.Event()
        self._slots = threading.BoundedSemaphore(8)
        self._load_repository()
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
        self._maintenance = threading.Thread(
            target=self._maintain, name="pyteg-host-maintenance", daemon=True
        )
        self._maintenance.start()

    def set_identity(self, user_id: int | None) -> None:
        """Asocia las confirmaciones de copia con la identidad autenticada local."""
        historical = (self._checkpoint or {}).get("checkpoint", {}).get("players")
        if historical and not any(player["userid"] == user_id for player in historical):
            return
        if type(user_id) is int and user_id > 0:
            self._user_id = user_id
            if self._session_id:
                with self._backup_lock:
                    self._bind_repository(self._session_id, user_id)

    def _bind_repository(self, session_id: str, user_id: int) -> None:
        if self._repository.bind_session(session_id, user_id):
            self._load_repository()

    def _load_repository(self) -> None:
        saved = self._repository.load()
        if saved is None or saved["kind"] != "game":
            return
        payload = saved["payload"]
        envelope = payload.get("envelope")
        if isinstance(envelope, dict) and (
            not envelope.get("durable")
            or (
                self._valid_proposal(envelope)
                and envelope.get("phase") == "committed"
                and joint_majority(envelope, envelope.get("certificate", []))
            )
        ):
            self._checkpoint = deepcopy(envelope)
            self._session_id = envelope["session_id"]
            self._user_id = payload.get("userid")
            election = payload.get("election")
            if isinstance(election, dict):
                self._election.restore(election)

    def join_room(self, session_id: str) -> None:
        """Conserva votos sólo al volver a la misma sala guardada."""
        with self._backup_lock:
            self._session_id = session_id
            if (
                self._checkpoint is not None
                and self._checkpoint["session_id"] == session_id
            ):
                return
            self._checkpoint = None
            self._pending = None
            self._election = ElectionState()
            self._session_id = session_id
            self._repository.start_room()
            if session_id and self._user_id is not None:
                self._bind_repository(session_id, self._user_id)

    def _maintain(self) -> None:
        while not self._stop.wait(1.0):
            server = self._server
            if server is not None:
                replication = server.host_replication
                if replication is not None and self._election.term > replication.epoch:
                    self._retire_authority(server)
                    continue
                if self.restored_waiting and not server.migration_sessions:
                    self.resume_restored_game()
                server.replicar_anfitrion()

    def _retire_authority(self, expected: Server) -> None:
        with self._lock:
            if self._server is not expected:
                return
            listener, grace, announcer = self._listener, self._grace, self._announcer
            self._server = None
            self._listener = None
            self._grace = None
            self._announcer = None
        if grace is not None:
            grace.cancel()
        if announcer is not None:
            announcer.close()
        if listener is not None:
            listener.close()
        expected.host_waiting_quorum = True
        expected.host_replication = None
        expected.detener()
        for client in expected.dame_clientes():
            client.cerrar()

    def resume_restored_game(self) -> None:
        """Retoma un guardado cuando volvieron todos o lo solicita el anfitrión."""
        server = self._server
        if self.restored_waiting and server is not None:
            self.restored_waiting = False
            self._engine.finish_recovery(server, server.host_resume_seconds)

    def _announce(self) -> None:
        try:
            self._announcer = RoomAnnouncer(self.room_announcement)
            self._announcer.start()
        except OSError as error:
            _LOG.debug("Descubrimiento LAN no disponible: %s", error)

    def room_announcement(self) -> dict[str, Any]:
        """Obtiene únicamente el anuncio público de la sala activa.

        Returns:
            Nombre, mapa, puerto y cantidad de jugadores.

        """
        server, listener = self._server, self._listener
        if server is None or listener is None or server.host_replication is None:
            return {}
        replication = server.host_replication
        players = server.dame_clientes()
        owner = next(
            (
                player.username()
                for player in players
                if player.userid() == replication.owner_id
            ),
            "Pyteg",
        )
        return {
            "message": "pyteg_room",
            "protocol": PROTOCOL_VERSION,
            "session_id": replication.session_id,
            "epoch": replication.epoch,
            "name": owner or "Pyteg",
            "theme": server.theme,
            "map_hash": server.map_hash(),
            "port": listener.port,
            "players": len(players),
            "state": server.estado.estado_actual(),
        }

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
            self.join_room("")
            server = self._engine.create(theme, rules_profile)
            try:
                listener = PlayerListener(server, self._bind_host, port)
            except OSError:
                server.detener()
                raise
            server.host_replication = HostReplication(
                server, self.store_checkpoint, transport=self
            )
            self._server, self._listener = server, listener
            listener.start()
            self._announce()
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
            or (self._session_id and self._session_id != envelope.get("session_id"))
        ):
            return False
        with self._backup_lock:
            if self._stop.is_set():
                return False
            self._bind_repository(
                envelope["session_id"], user_id or self._user_id or envelope["owner_id"]
            )
            if user_id is not None:
                self._user_id = user_id
            if envelope.get("durable") and (
                envelope.get("phase") != "committed"
                or not self._valid_proposal(envelope)
                or not joint_majority(envelope, envelope.get("certificate", []))
                or not self._election.authorize(envelope["epoch"], envelope["owner_id"])
            ):
                return False
            current = self._checkpoint
            if current is not None:
                if (current.get("durable") and not envelope.get("durable")) or current[
                    "session_id"
                ] != envelope["session_id"]:
                    return False
                if (envelope["epoch"], envelope["sequence"]) <= (
                    current["epoch"],
                    current["sequence"],
                ):
                    return False
            self._election.renew(envelope["epoch"], envelope["owner_id"])
            self._persist(envelope)
            self._checkpoint = deepcopy(envelope)
            self._session_id = envelope["session_id"]
            return True

    def can_follow(self, envelope: dict[str, Any]) -> bool:
        """Comprueba que la proyección no vuelva a una autoridad descartada.

        Returns:
            True si tenemos esa copia confirmada y no prometimos otra época.

        """
        with self._backup_lock:
            current = self._checkpoint
            return (
                current is not None
                and current["session_id"] == envelope["session_id"]
                and (current["epoch"], current["sequence"])
                >= (envelope["epoch"], envelope["sequence"])
                and envelope["epoch"] >= self._election.term
            )

    def _persist(self, envelope: dict[str, Any] | None = None) -> None:
        current = envelope if envelope is not None else self._checkpoint
        self._repository.save(
            make_archive(
                "game",
                {
                    "envelope": current,
                    "userid": self._user_id or (current or {}).get("owner_id"),
                    "pending": self._pending,
                    "election": self._election.export(),
                },
            )
        )

    @staticmethod
    def _valid_proposal(envelope: dict[str, Any]) -> bool:
        try:
            validate_client_event(envelope)
            body = {
                key: value
                for key, value in envelope.items()
                if key not in {"phase", "certificate", "digest"}
            }
            return (
                envelope.get("digest") == digest(body)
                and envelope.get("owner_id") in envelope.get("members", [])
                and bool(envelope.get("previous_members"))
            )
        except ValueError, TypeError:
            return False

    def stage_checkpoint(self, envelope: dict[str, Any]) -> bool:
        """Guarda una propuesta inerte antes de confirmar su recepción.

        Returns:
            True si quedó almacenada y su autoridad coincide con nuestros votos.

        """
        with self._backup_lock:
            if (
                self._stop.is_set()
                or not self._valid_proposal(envelope)
                or (self._session_id and self._session_id != envelope["session_id"])
            ):
                return False
            self._bind_repository(
                envelope["session_id"], self._user_id or envelope["owner_id"]
            )
            current = self._checkpoint
            if current is not None:
                if current["session_id"] != envelope["session_id"] or (
                    envelope["epoch"],
                    envelope["sequence"],
                ) < (current["epoch"], current["sequence"]):
                    return False
                if envelope["epoch"] > current["epoch"] and not majority(
                    current.get("members", [current["owner_id"]]),
                    envelope.get("election", []),
                ):
                    return False
            if not self._election.authorize(envelope["epoch"], envelope["owner_id"]):
                return False
            self._pending = deepcopy(envelope)
            self._persist()
            return True

    def commit_checkpoint(self, envelope: dict[str, Any]) -> bool:
        """Confirma únicamente la propuesta que ya se guardó en este participante.

        Returns:
            True si la copia confirmada está guardada para recuperación.

        """
        with self._backup_lock:
            if self._pending is None or self._pending.get("digest") != envelope.get(
                "digest"
            ):
                return False
            if not self._election.authorize(envelope["epoch"], envelope["owner_id"]):
                return False
            stored = self.store_checkpoint(envelope)
            if stored:
                self._pending = None
                self._persist()
            return stored

    def exchange(self, peer: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        """Realiza un RPC de copias con tamaño y duración acotados.

        Returns:
            Respuesta del participante o un diccionario vacío.

        """
        return self._query_peer(peer, request, timeout=_BACKUP_TIMEOUT)

    def _receive_backup(self, request: dict[str, Any], source: str) -> dict[str, Any]:
        envelope = request.get("envelope")
        if not isinstance(envelope, dict) or not self._valid_proposal(envelope):
            return {"accepted": False}
        if self._checkpoint is None:
            primary = self._primary
            if primary is None or source not in {
                primary[0],
                socket.gethostbyname(primary[0]),
            }:
                return {"accepted": False}
            player = next(
                (
                    player
                    for player in envelope["checkpoint"]["players"]
                    if player["userid"] == request.get("user_id")
                ),
                None,
            )
            if player is None or not secrets.compare_digest(
                player["token"], str(request.get("token", ""))
            ):
                return {"accepted": False}
        else:
            self._authenticate({**request, "epoch": self._checkpoint["epoch"]})
        accepted = (
            self.stage_checkpoint(envelope)
            if request["mensaje"] == "prepare_checkpoint"
            else self.commit_checkpoint(envelope)
        )
        return {
            "accepted": accepted,
            "userid": self._user_id,
            "digest": envelope["digest"],
        }

    def save_game(self, path: str | Path) -> None:
        """Guarda la última transición confirmada de la partida.

        Raises:
            ValueError: Si aún no hay una copia completa.

        """
        with self._lock:
            envelope = self.latest_checkpoint()
            if envelope is None:
                msg = "Todavía no hay una partida para guardar"
                raise ValueError(msg)
            write_archive(
                path,
                make_archive(
                    "game",
                    {
                        "envelope": envelope,
                        "userid": self._user_id or envelope["owner_id"],
                    },
                ),
            )

    def restore_game(self, path: str | Path, *, port: int = 0) -> tuple[int, int, str]:
        """Abre una copia guardada como una nueva sala recuperada.

        Returns:
            Puerto de juego, identidad local y token para recuperar su sesión.

        Raises:
            ValueError: Si el archivo no es compatible o ya existe un motor.
            OSError: Si no se puede leer o reservar el puerto.

        """
        payload = read_archive(path, kind="game")["payload"]
        envelope = payload.get("envelope")
        user_id = payload.get("userid")
        if not isinstance(envelope, dict) or not isinstance(user_id, int):
            msg = "El archivo no incluye una sesión recuperable"
            raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
        with self._lock:
            if self._server is not None or self._stop.is_set():
                msg = "Ya hay una partida abierta"
                raise ValueError(msg)
            checkpoint = envelope.get("checkpoint")
            if not isinstance(checkpoint, dict):
                msg = "Falta el estado de la partida"
                raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
            server = self._engine.restore(checkpoint)
            player = server.migration_sessions.get(user_id)
            if player is None:
                server.detener()
                msg = "La identidad guardada no pertenece a la partida"
                raise ValueError(msg)
            try:
                listener = PlayerListener(
                    server,
                    self._bind_host,
                    port,
                    first_user_id=max(server.migration_sessions, default=0) + 1,
                )
            except OSError:
                server.detener()
                raise
            server.host_migrating = True
            server.host_resume_seconds = checkpoint.get("remaining")
            self._user_id = user_id
            # Abrir un archivo crea una rama de sala; no compite con una sala
            # que pudiera seguir activa en otra computadora.
            self.join_room("")
            server.host_replication = HostReplication(
                server, self.store_checkpoint, owner_id=user_id, transport=self
            )
            self._server, self._listener = server, listener
            listener.start()
            self._announce()
            self.restored_waiting = True
            return listener.port, user_id, player.reconnect_token()

    def _schedule_grace(self, server: Server, remaining: int | None) -> None:
        self._grace = threading.Timer(
            MIGRATION_GRACE_SECONDS,
            lambda: self._engine.finish_recovery(server, remaining),
        )
        self._grace.daemon = True
        self._grace.start()

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
            self._primary_epoch = (
                (self._checkpoint or {}).get("epoch") if endpoint is not None else None
            )

    def recover(self, request: dict[str, Any]) -> dict[str, Any]:
        """Autoriza una promoción con el token de un jugador de la sala.

        Returns:
            Destino del anfitrión vigente o del nuevo anfitrión recuperado.

        Raises:
            ValueError: Si los datos no son compatibles o la sesión no es válida.

        """
        with self._lock:
            envelope = self._authenticate(request)
            server = self._server
            replication = server.host_replication if server is not None else None
            if (
                server is not None
                and replication is not None
                and replication.epoch < self._election.term
            ):
                self._retire_authority(server)
            if (
                self._server is None
                and self._primary is not None
                and self._primary_epoch == envelope["epoch"]
            ):
                return {
                    "mensaje": "host_alive",
                    "session_id": envelope["session_id"],
                    "epoch": envelope["epoch"],
                    "host": self._primary[0],
                    "port": self._primary[1],
                }
            if self._server is not None and self._server.host_waiting_quorum:
                authority = self._find_live_authority(envelope, request)
                if (
                    authority is not None
                    and authority.get("epoch", -1) > envelope["epoch"]
                ):
                    self._retire_authority(self._server)
                    return authority
            if self._server is None:
                envelope = self._freshest_checkpoint(envelope, request)
                authority = self._find_live_authority(envelope, request)
                if authority is not None:
                    return authority
                term, votes = self._elect(envelope, request)
                self._promote(envelope, term=term, votes=votes)
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
            or epoch > envelope["epoch"]
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
            "sequence": envelope["sequence"],
            "digest": envelope.get("digest"),
            "term": self._election.term,
        }
        if server is not None and listener is not None:
            replication = server.host_replication
            if replication is not None:
                if replication.epoch < self._election.term:
                    return response
                response.update(
                    mensaje="host_ready",
                    epoch=replication.epoch,
                    port=listener.port,
                    owner_id=replication.owner_id,
                )
        elif primary is not None and self._primary_epoch == envelope["epoch"]:
            response.update(mensaje="host_alive", host=primary[0], port=primary[1])
        return response

    def _freshest_checkpoint(
        self, envelope: dict[str, Any], request: dict[str, Any]
    ) -> dict[str, Any]:
        if not envelope.get("durable"):
            return envelope
        for peer in envelope["peers"]:
            if peer["userid"] == self._user_id:
                continue
            try:
                status = self._query_peer(peer, {**request, "mensaje": "host_status"})
                if (status.get("epoch", -1), status.get("sequence", -1)) <= (
                    envelope["epoch"],
                    envelope["sequence"],
                ):
                    continue
                backup = self.exchange(peer, {**request, "mensaje": "host_backup"}).get(
                    "envelope"
                )
                if (
                    not isinstance(backup, dict)
                    or not self._valid_proposal(backup)
                    or backup.get("phase") != "committed"
                    or backup.get("session_id") != envelope["session_id"]
                ):
                    continue
                if not joint_majority(backup, backup.get("certificate", [])):
                    continue
                with self._backup_lock:
                    self._persist(backup)
                    self._checkpoint = deepcopy(backup)
                    envelope = backup
            except OSError, ValueError, TypeError, FrameCodecError:
                continue
        return envelope

    def _grant_vote(self, request: dict[str, Any]) -> dict[str, Any]:
        envelope = self._authenticate(request)
        candidate, term = request.get("candidate"), request.get("term")
        members = envelope.get("members", [envelope["owner_id"]])
        accepted = False
        if type(candidate) is not int or type(term) is not int:
            return {"accepted": False, "term": self._election.term}
        with self._backup_lock:
            if (
                candidate in members
                and self._user_id in members
                and term > envelope["epoch"]
                and request.get("sequence", -1) >= envelope["sequence"]
                and self._election.vote(term, candidate)
            ):
                self._persist()
                accepted = True
        return {
            "accepted": accepted,
            "userid": self._user_id,
            "term": self._election.term,
        }

    def _elect(
        self, envelope: dict[str, Any], request: dict[str, Any]
    ) -> tuple[int, list[int]]:
        if not envelope.get("durable"):
            return envelope["epoch"] + 1, [self._user_id] if self._user_id else []
        term = max(self._election.term, envelope["epoch"]) + 1
        vote_request = {
            **request,
            "mensaje": "host_vote",
            "candidate": self._user_id,
            "term": term,
            "sequence": envelope["sequence"],
        }
        replies = [self._grant_vote(vote_request)]
        for peer in envelope["peers"]:
            if peer["userid"] == self._user_id:
                continue
            try:
                replies.append(self._query_peer(peer, vote_request))
            except OSError, ValueError, FrameCodecError:
                continue
        votes = [
            reply["userid"]
            for reply in replies
            if reply.get("accepted") is True and reply.get("term") == term
        ]
        if not majority(envelope["members"], votes):
            msg = "La recuperación espera una mayoría de participantes"
            raise ValueError(msg)
        return term, votes

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
                elif response.get("epoch", -1) < envelope["epoch"]:
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
    def _query_peer(
        peer: dict[str, Any],
        request: dict[str, Any],
        *,
        timeout: float = _PEER_STATUS_TIMEOUT,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        if isinstance(request.get("envelope"), dict):
            request = {**request, "envelope": encode_envelope(request["envelope"])}
        with socket.create_connection(
            (peer["host"], peer["port"]), timeout=timeout
        ) as conn:
            conn.sendall(NulDelimitedUtf8Codec.encode_frame(json.dumps(request)))
            codec = NulDelimitedUtf8Codec(_CONTROL_LIMIT)
            while time.monotonic() < deadline:
                conn.settimeout(max(0.01, deadline - time.monotonic()))
                data = conn.recv(65536)
                if not data:
                    break
                frames = codec.feed(data)
                if frames:
                    response = json.loads(frames[0])
                    if isinstance(response, dict):
                        if isinstance(response.get("envelope"), dict):
                            response["envelope"] = decode_envelope(response["envelope"])
                        return response
                    break
        return {}

    def _promote(
        self,
        envelope: dict[str, Any],
        *,
        term: int | None = None,
        votes: list[int] | None = None,
    ) -> None:
        checkpoint = envelope["checkpoint"]
        own_peer = next(
            (peer for peer in envelope["peers"] if peer["userid"] == self._user_id),
            None,
        )
        if own_peer is None:
            msg = "Este participante no está registrado como candidato"
            raise ValueError(msg)
        server = self._engine.restore(checkpoint)
        try:
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
            epoch=term if term is not None else envelope["epoch"] + 1,
            owner_id=own_peer["userid"],
            sequence=envelope["sequence"],
            peers=peers,
            transport=self if envelope.get("durable") else None,
            members=envelope.get("members"),
            election=votes,
        )
        self._server, self._listener = server, listener
        listener.start()
        self._announce()
        self._schedule_grace(server, checkpoint["remaining"])

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                conn, addr = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            if not self._slots.acquire(blocking=False):
                conn.close()
                continue
            threading.Thread(
                target=self._control, args=(conn, addr[0]), daemon=True
            ).start()

    def _control(self, conn: socket.socket, source: str) -> None:
        try:
            conn.settimeout(2.0)
            codec = NulDelimitedUtf8Codec(_CONTROL_LIMIT)
            frames: list[str] = []
            deadline = time.monotonic() + 2.0
            while not frames:
                conn.settimeout(max(0.01, deadline - time.monotonic()))
                if time.monotonic() >= deadline:
                    return
                data = conn.recv(65536)
                if not data:
                    return
                frames = codec.feed(data)
            request = json.loads(frames[0])
            if not isinstance(request, dict) or request.get("mensaje") not in {
                "recover_host",
                "host_status",
                "host_vote",
                "prepare_checkpoint",
                "commit_checkpoint",
                "host_backup",
            }:
                return
            if isinstance(request.get("envelope"), dict):
                request["envelope"] = decode_envelope(request["envelope"])
            handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
                "host_status": self.status,
                "host_vote": self._grant_vote,
                "recover_host": self.recover,
                "prepare_checkpoint": lambda data: self._receive_backup(data, source),
                "commit_checkpoint": lambda data: self._receive_backup(data, source),
                "host_backup": lambda data: {"envelope": self._authenticate(data)},
            }
            response = handlers[request["mensaje"]](request)
            if isinstance(response.get("envelope"), dict):
                response["envelope"] = encode_envelope(response["envelope"])
            conn.sendall(NulDelimitedUtf8Codec.encode_frame(json.dumps(response)))
        except (OSError, ValueError, KeyError, TypeError, FrameCodecError) as error:
            _LOG.debug("Solicitud de recuperación rechazada: %s", error)
        finally:
            conn.close()
            self._slots.release()

    def close(self) -> None:
        """Cierra listeners, temporizador y sockets al salir del cliente."""
        self._stop.set()
        if self._announcer is not None:
            self._announcer.close()
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
        self._maintenance.join(timeout=1.0)
