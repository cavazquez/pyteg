"""Tarea: canjear tres tarjetas por unidades generales."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.config import CARDS_FOR_EXCHANGE
from pyteg.exceptions import InvalidActionError, MissingFieldError
from pyteg.server.juego.validators import GameStateValidator, TurnValidator
from pyteg.server.tasks.base import LOGGER, IServerTask
from pyteg.server.tasks.types import CanjearTarjetasTaskData

if TYPE_CHECKING:
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol
    from pyteg.server.juego.game import Game


def _validar_seleccion_canje(simbolos: list[str]) -> None:
    if len(simbolos) != CARDS_FOR_EXCHANGE:
        msg = f"Debes seleccionar exactamente {CARDS_FOR_EXCHANGE} tarjetas"
        raise InvalidActionError(msg)
    unicos = len(set(simbolos))
    if unicos not in {1, CARDS_FOR_EXCHANGE}:
        msg = "Canje inválido: selecciona 3 del mismo símbolo o 3 símbolos distintos"
        raise InvalidActionError(msg)


def _resolver_tarjetas_jugador(
    tarjetas_payload: list[dict[str, Any]],
    tarjetas_asignadas: list[TarjetaDePais],
) -> list[TarjetaDePais]:
    seleccionadas: list[TarjetaDePais] = []
    for item in tarjetas_payload:
        pais = item.get("pais")
        simbolo = item.get("simbolo")
        if not isinstance(pais, str) or not isinstance(simbolo, str):
            msg = "Cada tarjeta debe incluir pais y simbolo válidos"
            raise InvalidActionError(msg)
        tarjeta = next(
            (
                t
                for t in tarjetas_asignadas
                if t.pais == pais and t.simbolo == simbolo and t not in seleccionadas
            ),
            None,
        )
        if tarjeta is None:
            msg = f"No posees la tarjeta {pais} ({simbolo})"
            raise InvalidActionError(msg)
        seleccionadas.append(tarjeta)
    return seleccionadas


class ServerTaskCanjearTarjetas(IServerTask[CanjearTarjetasTaskData]):
    """Tarea para canjear tres tarjetas por unidades."""

    def __init__(self, data: CanjearTarjetasTaskData) -> None:
        """Inicializa la tarea de canje de tarjetas.

        Args:
            data: Datos con la lista de tarjetas a canjear.

        """
        super().__init__(data)
        self._tarjetas_payload = data.get("tarjetas")
        self._action_name = "canjear_tarjetas"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        GameStateValidator.validate_game_started(context.game)
        if context.game is None:
            return

        TurnValidator.validate_turn(client, context.game)

        if self._tarjetas_payload is None:
            msg = "tarjetas"
            raise MissingFieldError(msg)

        if not isinstance(self._tarjetas_payload, list):
            msg = "El campo tarjetas debe ser una lista"
            raise InvalidActionError(msg)

        tarjetas_payload = cast("list[dict[str, Any]]", self._tarjetas_payload)
        game = cast("Game", context.game)
        tarjetas_asignadas = game.mazo().tarjetas_asignadas(client)
        tarjetas = _resolver_tarjetas_jugador(tarjetas_payload, tarjetas_asignadas)
        simbolos = [t.simbolo for t in tarjetas]
        _validar_seleccion_canje(simbolos)

        game.canjear(client, tarjetas)

        LOGGER.info(
            "Canje de tarjetas realizado por %s: %s",
            client.username(),
            [(t.pais, t.simbolo) for t in tarjetas],
        )

        context.enviar_tarjetas_jugador(client)
        context.enviar_unidades_disponibles()
        client.transmisor.enviar_sistema("Canje de tarjetas realizado exitosamente")
