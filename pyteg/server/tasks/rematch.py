"""Tarea de revancha que vuelve a abrir la sala sin reiniciar el proceso."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskVolverLobby(IServerTask[BaseTaskData]):
    """Permite al administrador iniciar otra partida con el mismo servidor."""

    requires_admin = True

    def __init__(self, data: BaseTaskData) -> None:
        """Inicializa la solicitud de revancha."""
        super().__init__(data)
        self._action_name = "volver_lobby"

    def _execute(self, client: IClientProtocol, _context: GameContext) -> bool:
        volver = getattr(client.server, "volver_al_lobby", None)
        if callable(volver) and not volver():
            client.transmisor.enviar_error(
                "invalid_state", "No hay una partida finalizada para repetir."
            )
            return False
        return True
