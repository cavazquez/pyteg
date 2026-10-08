"""Distribución de copias completas a candidatos a anfitrión autenticados."""

from __future__ import annotations

import json
import uuid
from operator import itemgetter
from typing import TYPE_CHECKING, Any

from pyteg.codecs_utils import DEFAULT_MAX_FRAME_BYTES
from pyteg.server.hosting.checkpoint import export_checkpoint

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.server.app import Server
    from pyteg.server.conexion.cliente import Client


class HostReplication:
    """Identidad de sala, época de autoridad y candidatos ordenados por userid."""

    def __init__(  # noqa: PLR0913 -- metadatos de autoridad recuperada.
        self,
        server: Server,
        store: Callable[[dict[str, Any]], object],
        *,
        session_id: str | None = None,
        epoch: int = 0,
        owner_id: int = 1,
        sequence: int = 0,
        peers: list[dict[str, Any]] | None = None,
    ) -> None:
        """Inicializa una sala nueva o la autoridad sucesora de una existente."""
        self.server = server
        self.session_id = session_id or uuid.uuid4().hex
        self.epoch = epoch
        self.owner_id = owner_id
        self.sequence = sequence
        self.peers = {peer["userid"]: dict(peer) for peer in peers or []}
        self._store = store
        self._subscribers: dict[int, Client] = {}

    def register(self, client: Client, port: int) -> None:
        """Registra el puerto y la dirección observada del participante."""
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
        }
        self._subscribers[client.userid()] = client

    def remove(self, user_id: int) -> None:
        """Retira un candidato que abandonó la sala del anfitrión activo."""
        self.peers.pop(user_id, None)
        self._subscribers.pop(user_id, None)

    def publish(self) -> None:
        """Publica datos privados únicamente a los candidatos que se registraron.

        Raises:
            ValueError: Si los datos no son compatibles o la sesión no es válida.

        """
        if not self._subscribers:
            return
        self.sequence += 1
        envelope = {
            "mensaje": "host_checkpoint",
            "session_id": self.session_id,
            "epoch": self.epoch,
            "owner_id": self.owner_id,
            "sequence": self.sequence,
            "recovering": self.server.host_migrating,
            "peers": sorted(self.peers.values(), key=itemgetter("userid")),
            "checkpoint": export_checkpoint(self.server),
        }
        payload = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
        if len(payload.encode("utf-8")) > DEFAULT_MAX_FRAME_BYTES:
            msg = "La copia de recuperación supera el límite TCP"
            raise ValueError(msg)
        self._store(envelope)
        for client in list(self._subscribers.values()):
            if client.handshake_status() is True:
                client.enviar(payload)
