"""Tarea: solicitar tarjetas del jugador."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.server.tasks.base import IServerTask

if TYPE_CHECKING:
    from pyteg.game_context import GameContext


class ServerTaskSolicitarTarjetas(IServerTask):
    """Tarea para solicitar las tarjetas del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de solicitar tarjetas.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)

    def _execute(self, client: Any, context: GameContext) -> None:
        """Envía las tarjetas del jugador al cliente que las solicita."""
        context.enviar_tarjetas_jugador(client)
