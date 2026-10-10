"""Replicación durable antes de confirmar acciones y cambios de membresía."""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from operator import itemgetter
from typing import TYPE_CHECKING, Any, Protocol

from pyteg.codecs_utils import DEFAULT_MAX_FRAME_BYTES
from pyteg.persistence.archive import digest
from pyteg.persistence.wire import encode_envelope
from pyteg.server.hosting.consensus import joint_majority

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.server.app import Server
    from pyteg.server.conexion.cliente import Client


class BackupTransport(Protocol):
    """Puerto de almacenamiento y RPC, independiente del motor."""

    def stage_checkpoint(self, envelope: dict[str, Any]) -> bool:
        """Conserva una propuesta sin hacerla elegible para recuperación."""
        ...

    def commit_checkpoint(self, envelope: dict[str, Any]) -> bool:
        """Conserva una copia confirmada y su certificado de mayoría."""
        ...

    def exchange(self, peer: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        """Envía una operación acotada al puerto de recuperación."""
        ...


class HostReplication:
    """Prepara, confirma y difunde una transición antes de aceptar su resultado."""

    def __init__(  # noqa: PLR0913 -- identidad y transporte del anfitrión recuperado.
        self,
        server: Server,
        store: Callable[[dict[str, Any]], object],
        *,
        session_id: str | None = None,
        epoch: int = 0,
        owner_id: int = 1,
        sequence: int = 0,
        peers: list[dict[str, Any]] | None = None,
        transport: BackupTransport | None = None,
        members: list[int] | None = None,
        election: list[int] | None = None,
    ) -> None:
        """Inicializa una autoridad nueva o sucesora con su grupo de votantes."""
        self.server = server
        self.session_id = session_id or uuid.uuid4().hex
        self.epoch = epoch
        self.owner_id = owner_id
        self.sequence = sequence
        self.peers = {peer["userid"]: dict(peer) for peer in peers or []}
        self.members = members or [owner_id]
        self.election = election or [owner_id]
        self._store = store
        self._transport = transport
        self._subscribers: dict[int, Client] = {}
        self._paused_remaining: int | None = None

    def register(self, client: Client, port: int) -> None:
        """Registra el puerto observado de un participante autenticado."""
        if (
            client.handshake_status() is not True
            or client.permite_migracion() is not True
            or client.es_reconexion_pendiente()
        ):
            return
        self.peers[client.userid()] = {
            "userid": client.userid(),
            "host": client.peer_host(),
            "port": port,
            "public_key": client.network_key(),
        }
        self._subscribers[client.userid()] = client

    def remove(self, user_id: int) -> None:
        """Retira un participante; la nueva membresía aún requiere confirmación."""
        self.peers.pop(user_id, None)
        self._subscribers.pop(user_id, None)

    def publish(self) -> bool:
        """Confirma la transición en mayorías de los grupos anterior y nuevo.

        Returns:
            True si la transición ya tiene copias durables suficientes.

        Raises:
            ValueError: Si la copia excede el límite del transporte.

        """
        self.sequence += 1
        checkpoint = self.server.capture_state()
        envelope: dict[str, Any] = {
            "mensaje": "host_checkpoint",
            "session_id": self.session_id,
            "epoch": self.epoch,
            "owner_id": self.owner_id,
            "sequence": self.sequence,
            "recovering": self.server.host_migrating,
            "peers": sorted(self.peers.values(), key=itemgetter("userid")),
            "checkpoint": checkpoint,
        }
        if self._transport is None:
            self._store(envelope)
            self._notify(envelope)
            return True
        envelope.update(
            durable=True,
            phase="prepared",
            members=sorted({self.owner_id, *self.peers}),
            previous_members=self.members,
            election=self.election,
        )
        envelope["digest"] = digest({
            key: value for key, value in envelope.items() if key != "phase"
        })
        payload = json.dumps(
            encode_envelope(envelope), ensure_ascii=False, separators=(",", ":")
        )
        if len(payload.encode("utf-8")) > DEFAULT_MAX_FRAME_BYTES:
            msg = "La copia de recuperación supera el límite TCP"
            raise ValueError(msg)
        if not self._transport.stage_checkpoint(envelope):
            self._set_waiting(waiting=True, remaining=checkpoint.get("remaining"))
            return False
        prepared = {self.owner_id, *self._broadcast("prepare_checkpoint", envelope)}
        if not joint_majority(envelope, prepared):
            self._set_waiting(waiting=True, remaining=checkpoint.get("remaining"))
            return False
        committed = {**envelope, "phase": "committed", "certificate": sorted(prepared)}
        if not self._transport.commit_checkpoint(committed):
            self._set_waiting(waiting=True, remaining=checkpoint.get("remaining"))
            return False
        confirmations = {
            self.owner_id,
            *self._broadcast("commit_checkpoint", committed),
        }
        if not joint_majority(envelope, confirmations):
            self._set_waiting(waiting=True, remaining=checkpoint.get("remaining"))
            return False
        self.members = list(envelope["members"])
        self._set_waiting(waiting=False)
        self._notify(committed)
        return True

    def _broadcast(self, message: str, envelope: dict[str, Any]) -> set[int]:
        transport = self._transport
        if transport is None:
            return set()
        owner = next(
            (
                player
                for player in envelope["checkpoint"]["players"]
                if player["userid"] == self.owner_id
            ),
            None,
        )
        if owner is None:
            return set()
        request = {
            "mensaje": message,
            "session_id": self.session_id,
            "epoch": self.epoch,
            "user_id": self.owner_id,
            "envelope": envelope,
        }
        peers = [
            peer for peer in self.peers.values() if peer["userid"] != self.owner_id
        ]
        if not peers:
            return set()

        def exchange(peer: dict[str, Any]) -> int | None:
            try:
                response = transport.exchange(peer, request)
                if (
                    response.get("accepted") is True
                    and response.get("digest") == envelope["digest"]
                    and response.get("userid") == peer["userid"]
                ):
                    return int(peer["userid"])
            except OSError, ValueError:
                return None
            return None

        with ThreadPoolExecutor(
            max_workers=len(peers), thread_name_prefix="pyteg-backup"
        ) as pool:
            return {
                user_id for user_id in pool.map(exchange, peers) if user_id is not None
            }

    def _notify(self, envelope: dict[str, Any]) -> None:
        payload = json.dumps(
            encode_envelope(envelope), ensure_ascii=False, separators=(",", ":")
        )
        for client in list(self._subscribers.values()):
            if client.handshake_status() is True:
                client.enviar(payload)

    def _set_waiting(self, *, waiting: bool, remaining: int | None = None) -> None:
        if self.server.host_waiting_quorum == waiting:
            return
        self.server.host_waiting_quorum = waiting
        if waiting:
            self._paused_remaining = remaining
            self.server.host_resume_seconds = remaining
            self.server.suspend_clock()
        elif not self.server.host_migrating:
            self.server.resume_clock(self._paused_remaining)
        payload = json.dumps({"mensaje": "host_availability", "paused": waiting})
        for client in list(self._subscribers.values()):
            client.enviar(payload)

    def unavailable(self) -> None:
        """Pausa las acciones también si falló el disco o el formato de una copia."""
        self._set_waiting(waiting=True, remaining=self.server.clock_remaining())
