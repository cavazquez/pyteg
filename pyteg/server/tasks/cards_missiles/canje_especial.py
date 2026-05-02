"""Tarea: canje especial (país + tarjeta -> 2 unidades en el país)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import SPECIAL_EXCHANGE_UNITS
from pyteg.exception import (
    CountryNotOwnedError,
    InvalidActionError,
    MissingFieldError,
)
from pyteg.server.juego.validators import GameStateValidator
from pyteg.server.tasks.base import IServerTask

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext


class ServerTaskCanjeEspecial(IServerTask):
    """Tarea para realizar un canje especial (país + tarjeta por 2 unidades)."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de canje especial.

        Args:
            data: Datos con el país para el canje.

        """
        super().__init__(data)
        self._pais = data.get("pais")
        self._action_name = "canje_especial"

    def _execute(self, client: Any, context: GameContext) -> None:
        """Ejecuta el canje especial de país + tarjeta por 2 unidades.

        Raises:
            MissingFieldError: Si el país no está especificado.
            CountryNotOwnedError: Si el jugador no posee el país.
            InvalidActionError: Si alguna validación falla.

        """
        GameStateValidator.validate_game_started(context.game)

        if self._pais is None:
            msg = "País"
            raise MissingFieldError(msg)

        if context.game is None:
            return

        mapa = context.game.mapa()
        mazo = context.game.mazo()

        if not mapa.jugador_posee_pais(client, self._pais):
            raise CountryNotOwnedError(self._pais)

        tarjeta_encontrada = None
        tarjetas_jugador = mazo.tarjetas_asignadas(client)  # type: ignore[attr-defined]

        if len(tarjetas_jugador) == 0:
            msg = "No tienes tarjetas. Conquista países para obtener tarjetas."
            raise InvalidActionError(msg)

        for tarjeta in tarjetas_jugador:
            if tarjeta.pais == self._pais:
                tarjeta_encontrada = tarjeta
                break

        if not tarjeta_encontrada:
            msg = f"No posees la tarjeta del país {self._pais}"
            raise InvalidActionError(msg)

        tarjeta_encontrada.desasignar()
        tarjeta_encontrada.desusar()

        for _ in range(SPECIAL_EXCHANGE_UNITS):
            mapa.agregar_una_unidad(self._pais)

        context.enviar_mapa()

        client.transmisor.enviar_canje_especial(self._pais, SPECIAL_EXCHANGE_UNITS)

        context.enviar_tarjetas_jugador(client)

        client.transmisor.enviar_sistema(
            f"Canje especial realizado: +{SPECIAL_EXCHANGE_UNITS} "
            f"unidades en {self._pais}"
        )
