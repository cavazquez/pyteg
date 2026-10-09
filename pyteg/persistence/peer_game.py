"""Réplica local que valida una transición usando las reglas compartidas."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101, TRY301

from __future__ import annotations

from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Any

from pyteg.persistence.archive import make_archive
from pyteg.persistence.in_process import InProcessGame
from pyteg.server.hosting.engine import ServerEngine

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.server.app import Server


class PeerGame(InProcessGame):
    """Motor sin listener de jugadores ni reloj que mute fuera del acuerdo."""

    def __init__(
        self,
        server: Server,
        user_id: int,
        *,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
    ) -> None:
        """Prepara una réplica y retiene eventos hasta confirmar la transición."""
        super().__init__(server, user_id, receive=receive)
        self.notifications: list[tuple[int, dict[str, Any]]] = []
        server.asynchronous = True
        server.suspend_clock()

    @classmethod
    def create(cls, theme: str, name: str, token: str, profile: str) -> PeerGame:
        """Crea el primer participante de una sala entre pares."""
        game = cls(ServerEngine().create(theme, profile), 1)
        try:
            player = game._player(1, name, reconnect_token=token)
            if not game.server.registrar_cliente(1, player):
                raise ValueError("No se pudo crear el primer participante")
        except Exception:
            game.close()
            raise
        return game

    @classmethod
    def from_checkpoint(
        cls, checkpoint: dict[str, Any], user_id: int, seed: int, timestamp: str
    ) -> PeerGame:
        """Reconstruye un motor candidato sin modificar la réplica confirmada."""
        game = cls(ServerEngine().restore(checkpoint), user_id)
        try:
            game.server.prepare_shared_transition(seed, timestamp)
            historical = dict(game.server.migration_sessions)
            connected = set(checkpoint["connected"])
            for player_id, previous in historical.items():
                if player_id not in connected:
                    continue
                player = game._player(
                    max(historical) + player_id,
                    previous.username(),
                    reconnect_token=previous.reconnect_token(),
                )
                game.server.registrar_reconexion_pendiente(player.userid(), player)
                restored = game.server.serialized(
                    partial(
                        game.server.reconectar_cliente,
                        player,
                        player_id,
                        previous.reconnect_token(),
                    )
                )
                if not restored:
                    raise ValueError("No se pudo reconstruir el participante")
            game.server.host_migrating = False
            # Reemplazar puertos locales reconstruye identidades; no representa
            # acciones nuevas en el historial de la partida.
            game.server.history.restore(checkpoint["history"])
            game.notifications.clear()
        except Exception:
            game.close()
            raise
        return game

    def _on_event(self, user_id: int, event: dict[str, Any]) -> None:
        if event.get("mensaje") == "command_result":
            self._events[event["command_id"]] = deepcopy(event)
        self.notifications.append((user_id, deepcopy(event)))

    def holder(self) -> int:
        """Obtiene el jugador activo o el administrador de la configuración."""
        turn = self.server.public_snapshot().get("turno")
        if isinstance(turn, dict):
            return int(turn["jugador_id"])
        return next(
            (
                player.userid()
                for player in self.server.dame_clientes()
                if player.es_admin()
            ),
            self.user_id,
        )

    def apply_operation(self, operation: dict[str, Any]) -> dict[str, Any] | None:
        """Valida una acción, alta, baja o vencimiento usando el motor normal."""
        kind = operation["kind"]
        if kind == "command":
            return self._apply_as(operation["actor"], operation["command"])
        if kind == "join":
            record = operation["member"]
            player = self._player(
                record["userid"], record["name"], reconnect_token=record["token"]
            )
            if not self.server.registrar_cliente(player.userid(), player):
                raise ValueError("La sala está llena o la identidad ya existe")
        elif kind == "rejoin":
            record = operation["member"]
            previous = next(
                (
                    item
                    for item in self.server.capture_state()["players"]
                    if item["userid"] == record["userid"]
                ),
                None,
            )
            if previous is None or previous["token"] != record["token"]:
                raise ValueError("La identidad no pertenece a esta partida")
            player = self._player(
                max(item["userid"] for item in self.server.capture_state()["players"])
                + 1,
                record["name"],
                reconnect_token=record["token"],
            )
            self.server.registrar_reconexion_pendiente(player.userid(), player)
            if not self.server.serialized(
                partial(
                    self.server.reconectar_cliente,
                    player,
                    record["userid"],
                    record["token"],
                )
            ):
                raise ValueError("No se pudo reconectar al participante")
        elif kind == "leave":
            self.server.quitarme(operation["target"])
        elif kind == "expire":
            snapshot = self.server.turno_snapshot()
            if snapshot is None:
                raise ValueError("No existe un turno para finalizar")
            self.server.encolar_vencimiento_turno(snapshot[1])
        else:
            raise ValueError("Operación de pares desconocida")
        self.server.serialized(lambda: None)
        return None

    def publish(self, receive: Callable[[int, dict[str, Any]], None]) -> None:
        """Entrega únicamente los eventos del jugador de esta ventana."""
        for user_id, event in self.notifications:
            if user_id == self.user_id:
                receive(user_id, event)
        self.notifications.clear()

    def sync_local(self) -> None:
        """Reconstruye la proyección privada del jugador conectado."""
        self.notifications.clear()
        super().sync_local()
        self.publish(self._receive)

    def draft(self) -> dict[str, Any]:
        """Obtiene el motor; la sesión añade los acuerdos y votos durables."""
        return make_archive(
            "game", {"peer_engine": self.server.capture_state(), "userid": self.user_id}
        )

    def close(self) -> None:
        """Descarta candidatos sin publicar ni guardar estados no confirmados."""
        if not self._closed:
            self._closed = True
            self.server.detener()
