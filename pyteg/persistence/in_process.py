"""Transporte en memoria compartido por partidas locales y por archivos."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from pyteg.persistence.archive import MemoryRepository
from pyteg.protocol_validation import validate_server_command
from pyteg.server.conexion.cliente import Client

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.persistence.archive import ArchiveRepository
    from pyteg.server.app import Server
    from pyteg.server.conexion.connection import ConnectionServer


class _LocalPort:
    """Entrega los mismos eventos privados y públicos que un socket."""

    def __init__(
        self, user_id: int, receive: Callable[[int, dict[str, Any]], None]
    ) -> None:
        self.user_id = user_id
        self.receive = receive
        self.owner: Client | None = None

    def send(self, data: str) -> None:
        """Conserva el destinatario incluso después de una reconexión."""
        self.receive(
            self.owner.userid() if self.owner is not None else self.user_id,
            json.loads(data),
        )


class InProcessGame:
    """Conecta jugadores al motor sin duplicar sus reglas ni tareas."""

    def __init__(
        self,
        server: Server,
        user_id: int,
        *,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> None:
        """Asocia el motor con el jugador visible y su almacenamiento."""
        self.server = server
        self.user_id = user_id
        self._receive = receive or (lambda _user, _event: None)
        self._repository = repository or MemoryRepository()
        self._events: dict[str, dict[str, Any]] = {}
        self._closed = False

    def _player(
        self, user_id: int, name: str, *, reconnect_token: str | None = None
    ) -> Client:
        port = _LocalPort(user_id, self._on_event)
        player = Client(
            user_id,
            cast("ConnectionServer", port),
            self.server,
            name,
            soy_admin=False,
            reconnect_token=reconnect_token,
        )
        port.owner = player
        player.marcar_handshake(True)  # noqa: FBT003
        return player

    def _restore_players(self) -> None:
        historical = dict(self.server.migration_sessions)
        for user_id, previous in historical.items():
            player = self._player(max(historical) + user_id, previous.username())
            self.server.registrar_reconexion_pendiente(player.userid(), player)
            if not self.server.serialized(
                partial(
                    self.server.reconectar_cliente,
                    player,
                    user_id,
                    previous.reconnect_token(),
                )
            ):
                msg = "No se pudo recuperar una identidad offline"
                raise ValueError(msg)
        if self.user_id not in historical:
            msg = "El destinatario no pertenece a esta partida"
            raise ValueError(msg)

    def _on_event(self, user_id: int, event: dict[str, Any]) -> None:
        if event.get("mensaje") == "command_result":
            self._events[event["command_id"]] = deepcopy(event)
        if user_id == self.user_id:
            self._receive(user_id, event)

    def holder(self) -> int:
        """Obtiene el jugador del turno o el administrador del lobby.

        Returns:
            Identidad que puede actuar.

        """
        snapshot = self.server.serialized(self.server.public_snapshot)
        turn = snapshot.get("turno")
        return int(turn["jugador_id"]) if isinstance(turn, dict) else self.user_id

    def _apply_as(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        data = dict(payload)
        data.setdefault("command_id", uuid.uuid4().hex)
        data = validate_server_command(data)
        if self._closed:
            msg = "La partida está cerrada"
            raise ValueError(msg)
        player = next(
            player
            for player in self.server.dame_clientes()
            if player.userid() == user_id
        )
        self.server.encolar_comando(player, data)
        self.server.serialized(lambda: None)
        return deepcopy(self._events.pop(data["command_id"], None))

    def apply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Aplica un comando validado del jugador local.

        Returns:
            Resultado de la acción si el protocolo lo confirma.

        """
        return self._apply_as(self.user_id, payload)

    def sync_player(self, user_id: int) -> None:
        """Envía datos públicos y sólo los datos privados de ese jugador."""
        self.server.serialized(partial(self._sync_player, user_id))

    def _sync_player(self, user_id: int) -> None:
        player = next(
            player
            for player in self.server.dame_clientes()
            if player.userid() == user_id
        )
        player.transmisor.enviar_userid(user_id)
        player.transmisor.enviar_session_token(user_id, player.reconnect_token())
        self.server.enviar_username()
        self.server.enviar_colores_asignados()
        player.transmisor.enviar_snapshot({
            **self.server.public_snapshot(),
            "resync": True,
        })
        if self.server.game is not None:
            self.server.enviar_tarjetas_jugador(player)
            self.server.enviar_objetivo_secreto(player)
            if self.holder() == user_id:
                self.server.enviar_unidades_disponibles()
        elif player.es_admin():
            player.transmisor.sos_admin()

    def sync_local(self) -> None:
        """Proyecta la identidad visible sobre el consumidor de la interfaz."""
        self.sync_player(self.user_id)

    def draft(self) -> dict[str, Any]:
        """Delega el formato del guardado a cada modo.

        Raises:
            NotImplementedError: Si un modo no define su formato.

        """
        raise NotImplementedError

    def save_draft(self) -> None:
        """Conserva el trabajo aceptado para continuar después de cerrar."""
        self._repository.save(self.draft())

    def close(self) -> None:
        """Guarda y detiene el motor local."""
        if not self._closed:
            try:
                self.save_draft()
            finally:
                self._closed = True
                self.server.detener()
