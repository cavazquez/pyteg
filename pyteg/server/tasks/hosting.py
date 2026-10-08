"""Registro de participantes capaces de recuperar la autoridad de la partida."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class HostCandidateData(BaseTaskData):
    """Puerto de recuperación ofrecido por un participante autenticado."""

    port: int


class ServerTaskHostCandidate(IServerTask[HostCandidateData]):
    """Registra un candidato sin cambiar las reglas ni la revisión pública."""

    def _execute(self, client: IClientProtocol, _context: GameContext) -> bool:
        replication = getattr(client.server, "host_replication", None)
        if replication is None:
            return False
        replication.register(client, self._data["port"])
        return True
