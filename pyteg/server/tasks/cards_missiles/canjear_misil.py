"""Tarea: canjear unidades por un misil en un país propio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.server.juego.validators import (
    CountryOwnershipValidator,
    GameStateValidator,
    PhaseValidator,
    TurnValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import CanjearMisilTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskCanjearMisil(IServerTask[CanjearMisilTaskData]):
    """Tarea para canjear unidades por un misil."""

    def _validate_field_not_none(self, field_value: Any, field_name: str) -> None:
        """Valida que un campo no sea None.

        Args:
            field_value: Valor del campo a validar.
            field_name: Nombre del campo para el mensaje de error.

        Raises:
            ValidationError: Si el campo es None.

        """
        if field_value is None:
            error_msg = f"{field_name} no especificado"
            raise ValidationError(error_msg)

    def __init__(self, data: CanjearMisilTaskData) -> None:
        """Inicializa la tarea de canjear misil.

        Args:
            data: Datos con el país donde canjear el misil.

        """
        super().__init__(data)
        self._pais: str | None = data.get("pais")
        self._action_name = "canjear_misil"

    def _validate_missiles_enabled(self, server: Any) -> None:
        """Valida que los misiles estén habilitados.

        Args:
            server: Instancia del servidor.

        Raises:
            ValidationError: Si los misiles no están habilitados.

        """
        if not server.misiles_habilitados():
            msg = "Los misiles no están habilitados en esta partida"
            raise ValidationError(msg)

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        self._validate_missiles_enabled(client.server)

        self._validate_field_not_none(self._pais, "País")

        if self._pais is None:
            return

        TurnValidator.validate_turn(client, context.game)
        GameStateValidator.validate_game_started(context.game)
        PhaseValidator.validate_command(context.game, "canjear_misil")

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._pais)

        rules = context.reglas()
        missile_cost = rules.missile_unit_cost
        is_shared = getattr(context.mapa, "es_condominio", None)
        shared = callable(is_shared) and is_shared(self._pais) is True
        # Un ocupante que canjea debe conservar al menos una unidad para que
        # el misil siga perteneciendo a un país que efectivamente ocupa.
        leave = (
            max(1, rules.missile_min_units_to_leave)
            if shared
            else rules.missile_min_units_to_leave
        )
        min_units = missile_cost + leave
        own_units = getattr(context.mapa, "cantidad_unidades_jugador", None)
        subtract_own = getattr(context.mapa, "restar_unidad_jugador", None)
        if shared and callable(own_units) and callable(subtract_own):
            userid = int(client.userid())
            available = own_units(self._pais, userid)
            if available < min_units:
                msg = (
                    f"Se requieren al menos {min_units} unidades propias "
                    f"para canjear un misil. {self._pais} tiene {available}."
                )
                raise ValidationError(msg)
            for _ in range(missile_cost):
                subtract_own(self._pais, userid)
        else:
            UnitValidator.validate_min_units(
                context.mapa,
                self._pais,
                min_units,
                (
                    f"Se requieren al menos {min_units} unidades "
                    f"para canjear un misil. {self._pais} tiene "
                    f"{context.mapa.cantidad_unidades(self._pais)} unidades."
                ),
            )
            for _ in range(missile_cost):
                context.mapa.restar_una_unidad(self._pais)

        context.mapa.agregar_misil(self._pais)
        cantidad_misiles = context.mapa.cantidad_misiles(self._pais)

        context.enviar_misil_agregado(self._pais, cantidad_misiles)
        context.enviar_mapa()

        client.transmisor.enviar_sistema(
            f"Misil canjeado en {self._pais}: -{missile_cost} unidades, +1 misil. "
            f"Total: {cantidad_misiles} misiles"
        )
