"""Tarea: atacar desde un país propio a un país adyacente enemigo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import MIN_UNITS_FOR_ATTACK
from pyteg.exceptions import MissingFieldError
from pyteg.server.juego.validators import (
    AdjacencyValidator,
    AttackRestrictionValidator,
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext


class ServerTaskAtacar(IServerTask):
    """Tarea para procesar ataques entre países."""

    def _validate_required_fields(self) -> None:
        """Valida que los campos requeridos estén presentes.

        Raises:
            ValidationError: Si algún campo requerido es None.

        """
        if self._origen is None:
            error_msg = "País de origen no especificado"
            raise ValidationError(error_msg)
        if self._destino is None:
            error_msg = "País de destino no especificado"
            raise ValidationError(error_msg)

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de atacar.

        Args:
            data: Datos con país de origen, destino y cantidad de unidades.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad_unidades = data.get("cantidad_unidades")
        self._action_name = "atacar"

    def _execute(self, client: Any, context: GameContext) -> None:
        self._validate_required_fields()

        if self._cantidad_unidades is None:
            msg = "Cantidad de unidades"
            raise MissingFieldError(msg)

        if self._origen is None or self._destino is None:
            return

        GameStateValidator.validate_game_started(context.game)

        if context.game is None:
            return
        AttackRestrictionValidator.validate_not_first_turns(context.game)

        TurnValidator.validate_turn(client, context.game)

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._origen)

        CountryOwnershipValidator.validate_not_own_country(
            client, context.mapa, self._destino
        )

        AdjacencyValidator.validate_adjacent(context.mapa, self._origen, self._destino)

        UnitValidator.validate_min_units(
            context.mapa,
            self._origen,
            MIN_UNITS_FOR_ATTACK,
            f"Necesitas al menos {MIN_UNITS_FOR_ATTACK} unidades en "
            f"{self._origen} para atacar",
        )

        unidades_origen = context.mapa.cantidad_unidades(self._origen)
        unidades_destino = context.mapa.cantidad_unidades(self._destino)
        LOGGER.info("=== INICIO ATAQUE ===")
        LOGGER.info(
            "Origen: %s (%s unidades)",
            self._origen,
            unidades_origen,
        )
        LOGGER.info(
            "Destino: %s (%s unidades)",
            self._destino,
            unidades_destino,
        )
        LOGGER.info("Cantidad unidades atacando: %s", self._cantidad_unidades)

        if context.game is None:
            return
        info_batalla = context.game.atacar(
            self._origen, self._destino, self._cantidad_unidades
        )

        unidades_origen_post = context.mapa.cantidad_unidades(self._origen)
        unidades_destino_post = context.mapa.cantidad_unidades(self._destino)
        LOGGER.info("=== RESULTADO ATAQUE ===")
        LOGGER.info(
            "Origen: %s (%s -> %s unidades)",
            self._origen,
            unidades_origen,
            unidades_origen_post,
        )
        LOGGER.info(
            "Destino: %s (%s -> %s unidades)",
            self._destino,
            unidades_destino,
            unidades_destino_post,
        )
        LOGGER.info("Conquistado: %s", info_batalla["conquistado"])
        cantidad_texto = (
            f" con {self._cantidad_unidades} unidades"
            if self._cantidad_unidades is not None
            else ""
        )
        LOGGER.info(
            "Ataque realizado de %s a %s%s",
            self._origen,
            self._destino,
            cantidad_texto,
        )

        context.enviar_mapa()

        batalla_data = {
            "origen": self._origen,
            "destino": self._destino,
            "atacante": info_batalla["atacante"],
            "defensor": info_batalla["defensor"],
            "dados_atacante": info_batalla["dados_atacante"],
            "dados_defensor": info_batalla["dados_defensor"],
            "resultado": info_batalla["resultado"],
            "conquistado": info_batalla["conquistado"],
        }
        context.enviar_resultado_batalla(batalla_data)

        if info_batalla["conquistado"]:
            LOGGER.info(
                "%s conquistó %s - puede reclamar tarjeta",
                client.username(),
                self._destino,
            )
            if context.game is not None:
                context.game.marcar_jugador_puede_reclamar(client)
