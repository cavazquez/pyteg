# ruff: noqa: C901, PLR0912, PLR0914, PLR0915, TRY003, EM101, PLR2004

"""Tarea: atacar desde un país propio a un país adyacente enemigo."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from pyteg.config import MIN_UNITS_FOR_ATTACK
from pyteg.exceptions import MissingFieldError
from pyteg.server.juego.validators import (
    AdjacencyValidator,
    AttackRestrictionValidator,
    CountryOwnershipValidator,
    GameStateValidator,
    PhaseValidator,
    TurnValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask
from pyteg.server.tasks.types import AtacarTaskData

_POSITIONAL_PARAMETER_KINDS = frozenset({
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
})
_RECLAMO_COUNTRY_PARAMETER_COUNT = 2

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol
    from pyteg.server.msg.types import BattleResultPayload


class ServerTaskAtacar(IServerTask[AtacarTaskData]):
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

    def __init__(self, data: AtacarTaskData) -> None:
        """Inicializa la tarea de atacar.

        Args:
            data: Datos con país de origen, destino y cantidad de unidades.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad_unidades = data.get("cantidad_unidades")
        self._objetivo_jugador = data.get("objetivo_jugador")
        self._action_name = "atacar"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        self._validate_required_fields()

        if self._cantidad_unidades is None:
            msg = "Cantidad de unidades"
            raise MissingFieldError(msg)

        if self._origen is None or self._destino is None:
            return

        GameStateValidator.validate_game_started(context.game)
        PhaseValidator.validate_command(context.game, "atacar")

        if context.game is None:
            return
        AttackRestrictionValidator.validate_not_first_turns(context.game)

        TurnValidator.validate_turn(client, context.game)

        validar_accion = getattr(context.game, "validar_accion_situacion", None)
        if callable(validar_accion):
            validar_accion(client, "atacar")

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._origen)

        destino_compartido = getattr(context.mapa, "es_condominio", None)
        es_compartido = callable(destino_compartido) and bool(
            destino_compartido(self._destino)
        )
        if es_compartido:
            ocupantes: dict[int, int] = getattr(
                context.mapa, "ocupantes", lambda _pais: {}
            )(self._destino)
            if self._objetivo_jugador is None:
                raise ValidationError(
                    "Un país en condominio requiere indicar el ocupante objetivo"
                )
            if int(self._objetivo_jugador) not in ocupantes:
                raise ValidationError("El jugador indicado no ocupa el país objetivo")
            if int(self._objetivo_jugador) == int(client.userid()):
                raise ValidationError("No puedes atacar tus propias unidades")
        else:
            CountryOwnershipValidator.validate_not_own_country(
                client, context.mapa, self._destino
            )

        AdjacencyValidator.validate_adjacent(context.mapa, self._origen, self._destino)

        validar_ataque = getattr(context.game, "validar_ataque_situacion", None)
        if callable(validar_ataque):
            validar_ataque(self._origen, self._destino)
        validar_pacto = getattr(context.game, "validar_pacto_ataque", None)
        if callable(validar_pacto):
            validar_pacto(
                client,
                self._origen,
                self._destino,
                self._objetivo_jugador,
            )

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
        atacar = context.game.atacar
        parametros = inspect.signature(atacar).parameters.values()
        acepta_participantes = (
            any(
                parametro.kind is inspect.Parameter.VAR_POSITIONAL
                for parametro in parametros
            )
            or sum(
                parametro.kind in _POSITIONAL_PARAMETER_KINDS
                for parametro in parametros
            )
            >= 5
        )
        if acepta_participantes:
            info_batalla = atacar(
                self._origen,
                self._destino,
                self._cantidad_unidades,
                int(client.userid()),
                self._objetivo_jugador,
            )
        else:
            info_batalla = atacar(
                self._origen,
                self._destino,
                self._cantidad_unidades,
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

        batalla_data: BattleResultPayload = {
            "origen": self._origen,
            "destino": self._destino,
            "atacante": info_batalla["atacante"],
            "defensor": info_batalla["defensor"],
            "atacante_id": info_batalla.get("atacante_id"),
            "defensor_id": info_batalla.get("defensor_id"),
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
                marcar_reclamo = context.game.marcar_jugador_puede_reclamar
                parametros = inspect.signature(marcar_reclamo).parameters.values()
                acepta_pais = (
                    any(
                        parametro.kind is inspect.Parameter.VAR_POSITIONAL
                        for parametro in parametros
                    )
                    or sum(
                        parametro.kind in _POSITIONAL_PARAMETER_KINDS
                        for parametro in parametros
                    )
                    >= _RECLAMO_COUNTRY_PARAMETER_COUNT
                )
                if acepta_pais:
                    marcar_reclamo(client, self._destino)
                else:
                    # Compatibility with older game doubles/servers that only
                    # tracked the generic per-turn card eligibility.
                    marcar_reclamo(client)
