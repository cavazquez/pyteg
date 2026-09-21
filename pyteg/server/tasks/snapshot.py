"""Tarea para resincronizar el estado público de una conexión."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskSolicitarSnapshot(IServerTask[BaseTaskData]):
    """Reenvía la revisión actual sin mutar la partida."""

    def _execute(self, client: IClientProtocol, _context: GameContext) -> None:
        enviar = getattr(client.server, "public_snapshot", None)
        if callable(enviar):
            snapshot = dict(enviar())
            snapshot["resync"] = True
            client.transmisor.enviar_snapshot(snapshot)
