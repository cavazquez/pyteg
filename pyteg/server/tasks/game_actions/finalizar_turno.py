"""Tarea: finalizar el turno actual."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.juego.validators import TurnValidator
from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import BaseTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskFinalizarTurno(IServerTask[BaseTaskData]):
    """Tarea para finalizar el turno de un jugador."""

    def __init__(self, data: BaseTaskData) -> None:
        """Inicializa la tarea de finalizar turno.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        TurnValidator.validate_turn(client, context.game)

        if context.game is not None:
            context.game.limpiar_elegibilidad_reclamar()

            context.game.finalizar_turno()

        context.enviar_turno_actual()
        context.enviar_mapa()
