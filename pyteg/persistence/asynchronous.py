"""Partidas por archivos de turno, con el mismo motor y sin sockets."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from pyteg.persistence.archive import (
    ArchiveRepository,
    MemoryRepository,
    make_archive,
    validate_archive,
)
from pyteg.protocol_validation import validate_server_command
from pyteg.server.conexion.cliente import Client
from pyteg.server.hosting.engine import ServerEngine

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.server.app import Server
    from pyteg.server.conexion.connection import ConnectionServer

_READ_ONLY = frozenset({"chat", "solicitar_snapshot", "solicitar_tarjetas"})
_MAX_PLAYERS = 8
_MAX_PLAYER_NAME = 80
_MAX_TURN_CHAIN = 4096
_HASH_LENGTH = 64


class _LocalPort:
    """Adaptador de salida del motor hacia un consumidor local."""

    def __init__(
        self, user_id: int, receive: Callable[[int, dict[str, Any]], None]
    ) -> None:
        self.user_id = user_id
        self.receive = receive
        self.owner: Client | None = None

    def send(self, data: str) -> None:
        self.receive(
            self.owner.userid() if self.owner is not None else self.user_id,
            json.loads(data),
        )


class AsyncGame:
    """Una copia editable únicamente por el destinatario del turno actual."""

    def __init__(
        self,
        server: Server,
        user_id: int,
        *,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> None:
        """Asocia el motor offline con la identidad local y su almacenamiento."""
        self.server = server
        self.user_id = user_id
        self.session_id = uuid.uuid4().hex
        self.step = 0
        self.base_id: str | None = None
        self.ancestors: list[str] = []
        self.handed_off = False
        self._last_packet: dict[str, Any] | None = None
        self._receive = receive or (lambda _user, _event: None)
        self._repository = repository or MemoryRepository()
        self._events: dict[str, dict[str, Any]] = {}
        self._closed = False
        server.asynchronous = True
        server.suspend_clock()

    @classmethod
    def create(
        cls,
        theme: str,
        names: list[str],
        *,
        rules_profile: str | None = None,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> AsyncGame:
        """Crea un lobby offline de uno a ocho jugadores.

        Returns:
            Partida administrada inicialmente por el primer jugador.

        Raises:
            ValueError: Si la lista de jugadores no es válida.

        """
        if not 1 <= len(names) <= _MAX_PLAYERS or any(
            not name.strip() or len(name) > _MAX_PLAYER_NAME for name in names
        ):
            msg = "Elegí entre uno y ocho nombres de jugador"
            raise ValueError(msg)
        server = ServerEngine().create(theme, rules_profile)
        session = cls(server, 1, receive=receive, repository=repository)
        try:
            for user_id, name in enumerate(names, 1):
                player = session._player(user_id, name.strip())
                if not server.registrar_cliente(user_id, player):
                    msg = "No se pudo registrar al jugador"
                    raise ValueError(msg)  # noqa: TRY301 -- cierra el motor ante error.
            session.save_draft()
        except Exception:
            server.detener()
            raise
        return session

    @classmethod
    def open(
        cls,
        archive: dict[str, Any],
        *,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> AsyncGame:
        """Abre un turno compartido o un borrador local guardado.

        Returns:
            Copia local validada, sin temporizador ni red.

        Raises:
            ValueError: Si el archivo o su destinatario no son válidos.

        """
        archive = validate_archive(archive)
        payload = archive["payload"]
        if archive["kind"] == "turn":
            cls._validate_turn(payload)
            metadata = {
                "userid": payload["holder"],
                "session_id": payload["session_id"],
                "step": payload["step"],
                "base_id": archive["sha256"],
                "ancestors": payload["ancestors"],
                "handed_off": False,
                "last_packet": None,
            }
        elif archive["kind"] == "game" and isinstance(payload.get("async"), dict):
            metadata = payload["async"]
        else:
            msg = "Este archivo no es una partida asíncrona"
            raise ValueError(msg)
        cls._validate_metadata(metadata)
        if not isinstance(payload.get("checkpoint"), dict):
            msg = "Falta el estado de la partida asíncrona"
            raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
        server = ServerEngine().restore(payload["checkpoint"])
        session = cls(
            server, metadata["userid"], receive=receive, repository=repository
        )
        try:
            session.session_id = metadata["session_id"]
            session.step = metadata["step"]
            session.base_id = metadata["base_id"]
            session.ancestors = list(metadata["ancestors"])
            session.handed_off = metadata["handed_off"]
            session._last_packet = metadata.get("last_packet")
            historical = dict(server.migration_sessions)
            for user_id, previous in historical.items():
                player = session._player(max(historical) + user_id, previous.username())
                server.registrar_reconexion_pendiente(player.userid(), player)
                if not server.serialized(
                    partial(
                        server.reconectar_cliente,
                        player,
                        user_id,
                        previous.reconnect_token(),
                    )
                ):
                    msg = "No se pudo recuperar una identidad offline"
                    raise ValueError(msg)  # noqa: TRY301 -- restaura de forma transaccional.
            if session.user_id not in historical:
                msg = "El destinatario no pertenece a esta partida"
                raise ValueError(msg)  # noqa: TRY301 -- restaura de forma transaccional.
            if archive["kind"] == "turn" and session.holder() != session.user_id:
                msg = "El archivo no corresponde al jugador del turno"
                raise ValueError(msg)  # noqa: TRY301 -- restaura de forma transaccional.
            session.save_draft()
        except Exception:
            server.detener()
            raise
        return session

    @staticmethod
    def _validate_metadata(metadata: dict[str, Any]) -> None:
        ancestors = metadata.get("ancestors")
        base = metadata.get("base_id")
        checks = (
            type(metadata.get("userid")) is int,
            metadata.get("userid", 0) > 0
            if type(metadata.get("userid")) is int
            else False,
            isinstance(metadata.get("session_id"), str)
            and bool(metadata.get("session_id")),
            type(metadata.get("step")) is int,
            isinstance(ancestors, list),
            type(metadata.get("handed_off")) is bool,
            base is None or (isinstance(base, str) and len(base) == _HASH_LENGTH),
        )
        if not all(checks) or not isinstance(ancestors, list):
            msg = "Borrador asíncrono inválido"
            raise ValueError(msg)
        if metadata["step"] != len(ancestors) or len(ancestors) > _MAX_TURN_CHAIN:
            msg = "Cadena del borrador asíncrono inválida"
            raise ValueError(msg)
        if any(
            not isinstance(item, str) or len(item) != _HASH_LENGTH for item in ancestors
        ):
            msg = "Referencias del borrador asíncrono inválidas"
            raise ValueError(msg)
        packet = metadata.get("last_packet")
        if packet is not None:
            packet = validate_archive(packet, kind="turn")
            AsyncGame._validate_turn(packet["payload"])
            if (
                packet["payload"]["session_id"] != metadata["session_id"]
                or packet["payload"]["author"] != metadata["userid"]
                or not metadata["handed_off"]
            ):
                msg = "La última entrega no corresponde al borrador"
                raise ValueError(msg)

    @staticmethod
    def _validate_turn(payload: dict[str, Any]) -> None:
        ancestors = payload.get("ancestors")
        if not isinstance(ancestors, list):
            msg = "Cadena de turnos inválida"
            raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
        checks = (
            isinstance(payload.get("session_id"), str)
            and bool(payload.get("session_id")),
            len(ancestors) <= _MAX_TURN_CHAIN,
            all(
                isinstance(item, str) and len(item) == _HASH_LENGTH
                for item in ancestors
            ),
            type(payload.get("step")) is int,
            payload.get("step") == len(ancestors),
            payload.get("parent") == (ancestors[-1] if ancestors else None),
            type(payload.get("holder")) is int,
            type(payload.get("author")) is int,
            isinstance(payload.get("checkpoint"), dict),
        )
        if not all(checks) or len(set(ancestors)) != len(ancestors):
            msg = "Cadena de turnos inválida"
            raise ValueError(msg)

    def _player(self, user_id: int, name: str) -> Client:
        port = _LocalPort(user_id, self._on_event)
        player = Client(
            user_id,
            cast("ConnectionServer", port),
            self.server,
            name,
            soy_admin=False,
        )
        port.owner = player
        player.marcar_handshake(True)  # noqa: FBT003
        return player

    def _on_event(self, user_id: int, event: dict[str, Any]) -> None:
        if user_id == self.user_id:
            if event.get("mensaje") == "command_result":
                self._events[event["command_id"]] = deepcopy(event)
            self._receive(user_id, event)

    def holder(self) -> int:
        """Obtiene el destinatario actual.

        Returns:
            Jugador del turno o administrador mientras se configura.

        """
        turn = self.server.public_snapshot().get("turno")
        return int(turn["jugador_id"]) if isinstance(turn, dict) else self.user_id

    def apply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Valida un comando y lo aplica con las mismas tareas que usa TCP.

        Returns:
            Confirmación correlacionada de la acción.

        Raises:
            ValueError: Si la copia ya se entregó o el turno pertenece a otro.

        """
        data = dict(payload)
        data.setdefault("command_id", uuid.uuid4().hex)
        data = validate_server_command(data)
        if self._closed:
            msg = "La partida está cerrada"
            raise ValueError(msg)
        if data["mensaje"] not in _READ_ONLY and (
            self.handed_off or self.holder() != self.user_id
        ):
            msg = "Este turno ya se entregó o pertenece a otro jugador"
            raise ValueError(msg)
        player = next(
            player
            for player in self.server.dame_clientes()
            if player.userid() == self.user_id
        )
        self.server.encolar_comando(player, data)
        self.server.serialized(lambda: None)
        result = self._events.get(data["command_id"])
        if (
            result is not None
            and result.get("accepted")
            and data["mensaje"] == "finalizar_turno"
        ):
            self.handed_off = True
        self.save_draft()
        return deepcopy(result)

    def draft(self) -> dict[str, Any]:
        """Captura la copia de trabajo local, que conserva su identidad.

        Returns:
            Archivo de guardado asíncrono.

        """
        return make_archive(
            "game",
            {
                "checkpoint": self.server.capture_state(),
                "async": {
                    "userid": self.user_id,
                    "session_id": self.session_id,
                    "step": self.step,
                    "base_id": self.base_id,
                    "ancestors": self.ancestors,
                    "handed_off": self.handed_off,
                    "last_packet": self._last_packet,
                },
            },
        )

    def save_draft(self) -> None:
        """Conserva el trabajo aceptado para continuar después de cerrar."""
        self._repository.save(self.draft())

    def export_turn(self) -> dict[str, Any]:
        """Sella el turno terminado para compartirlo una sola vez.

        Returns:
            El mismo archivo en cada exportación repetida de ese turno.

        Raises:
            ValueError: Si todavía se está jugando el turno local.

        """
        if self._last_packet is not None:
            return deepcopy(self._last_packet)
        if (
            not self.server.estado.es_jugando()
            and not self.server.estado.es_finalizado()
        ):
            msg = "Primero configurá e iniciá la partida"
            raise ValueError(msg)
        if (
            not self.handed_off
            and self.holder() == self.user_id
            and not self.server.estado.es_finalizado()
        ):
            msg = "Finalizá tu turno antes de exportarlo"
            raise ValueError(msg)
        ancestors = [*self.ancestors, *([self.base_id] if self.base_id else [])]
        self._last_packet = make_archive(
            "turn",
            {
                "session_id": self.session_id,
                "step": len(ancestors),
                "parent": self.base_id,
                "ancestors": ancestors,
                "author": self.user_id,
                "holder": self.holder(),
                "checkpoint": self.server.capture_state(),
            },
        )
        self.handed_off = True
        self.save_draft()
        return deepcopy(self._last_packet)

    def can_export(self) -> bool:
        """Indica si la copia está lista para entregar.

        Returns:
            True al terminar el turno o al preparar la primera entrega.

        """
        return self._last_packet is not None or (
            (self.server.estado.es_jugando() or self.server.estado.es_finalizado())
            and (
                self.handed_off
                or self.holder() != self.user_id
                or self.server.estado.es_finalizado()
            )
        )

    def check_successor(self, archive: dict[str, Any]) -> bool:
        """Detecta duplicados, archivos atrasados y ramas incompatibles.

        Returns:
            False si el archivo ya estaba abierto; True si continúa esta copia.

        Raises:
            ValueError: Si pertenece a otra partida o a una rama distinta.

        """
        archive = validate_archive(archive, kind="turn")
        payload = archive["payload"]
        self._validate_turn(payload)
        if archive["sha256"] == self.base_id:
            return False
        boundary = self._last_packet["sha256"] if self._last_packet else self.base_id
        if payload["session_id"] != self.session_id or (
            boundary is not None and boundary not in payload["ancestors"]
        ):
            msg = "El archivo pertenece a otra partida o a una continuación distinta"
            raise ValueError(msg)
        if payload["holder"] != self.user_id:
            msg = "Este archivo está destinado a otro jugador"
            raise ValueError(msg)
        return True

    def sync_local(self) -> None:
        """Proyecta identidad, estado y datos privados del jugador local."""
        player = next(
            player
            for player in self.server.dame_clientes()
            if player.userid() == self.user_id
        )
        player.transmisor.enviar_userid(self.user_id)
        player.transmisor.enviar_session_token(self.user_id, player.reconnect_token())
        self.server.enviar_username()
        self.server.enviar_colores_asignados()
        player.transmisor.enviar_snapshot({
            **self.server.public_snapshot(),
            "resync": True,
        })
        if self.server.game is not None:
            self.server.enviar_tarjetas_jugador(player)
            self.server.enviar_objetivo_secreto(player)
            if self.holder() == self.user_id:
                self.server.enviar_unidades_disponibles()
        elif player.es_admin():
            player.transmisor.sos_admin()

    def close(self) -> None:
        """Guarda y detiene el motor offline."""
        if not self._closed:
            try:
                self.save_draft()
            finally:
                self._closed = True
                self.server.detener()
