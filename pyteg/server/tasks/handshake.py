"""Negociación explícita de protocolo y mapa."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskHello(IServerTask[BaseTaskData]):
    """Acepta o rechaza el contrato anunciado por un cliente."""

    def _execute(self, client: IClientProtocol, _context: GameContext) -> bool:
        validar = getattr(client.server, "validar_handshake", None)
        if callable(validar):
            return bool(validar(client, dict(self._data)))
        return True
