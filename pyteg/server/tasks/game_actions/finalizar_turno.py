"""Tarea: finalizar el turno actual."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.server.juego.validators import TurnValidator
from pyteg.server.tasks.base import IServerTask

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext


class ServerTaskFinalizarTurno(IServerTask):
    """Tarea para finalizar el turno de un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de finalizar turno.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client: Any, context: GameContext) -> None:
        TurnValidator.validate_turn(client, context.game)

        if context.game is not None:
            context.game.limpiar_elegibilidad_reclamar()

            context.game.finalizar_turno()

        context.enviar_turno_actual()
        context.enviar_mapa()
