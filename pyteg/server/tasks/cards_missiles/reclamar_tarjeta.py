"""Tarea: reclamar tarjeta tras conquistar un país en el turno."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.exception import InvalidActionError
from pyteg.server.juego.validators import GameStateValidator, TurnValidator
from pyteg.server.tasks.base import LOGGER, IServerTask

if TYPE_CHECKING:
    from pyteg.game_context import GameContext


class ServerTaskReclamarTarjeta(IServerTask):
    """Tarea para reclamar una tarjeta después de conquistar un país."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de reclamar tarjeta.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "reclamar_tarjeta"

    def _execute(self, client: Any, context: GameContext) -> None:
        """Reclama una tarjeta si el jugador conquistó un país en este turno.

        Raises:
            InvalidActionError: Si el jugador no puede reclamar tarjeta.

        """
        GameStateValidator.validate_game_started(context.game)

        if context.game is None:
            return

        TurnValidator.validate_turn(client, context.game)

        if not context.game.puede_reclamar_tarjeta(client):
            msg = "No has conquistado ningún país en este turno"
            raise InvalidActionError(msg)

        LOGGER.info("Asignando tarjeta a %s por reclamación manual", client.username())
        context.game.dame_una_tarjeta(client)

        context.game.reclamar_tarjeta_jugador(client)

        context.enviar_tarjetas_jugador(client)

        client.transmisor.enviar_sistema("Tarjeta reclamada exitosamente")
