"""Tarea: solicitar tarjetas del jugador."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskSolicitarTarjetas(IServerTask[BaseTaskData]):
    """Tarea para solicitar las tarjetas del jugador."""

    def __init__(self, data: BaseTaskData) -> None:
        """Inicializa la tarea de solicitar tarjetas.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        """Envía las tarjetas del jugador al cliente que las solicita."""
        context.enviar_tarjetas_jugador(client)
