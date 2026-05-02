"""Tarea: canjear unidades por un misil en un país propio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import MISSILE_UNIT_COST
from pyteg.server.juego.validators import (
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import IServerTask

if TYPE_CHECKING:
    from pyteg.game_context import GameContext


class ServerTaskCanjearMisil(IServerTask):
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

    def __init__(self, data: dict[str, Any]) -> None:
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

    def _execute(self, client: Any, context: GameContext) -> None:
        self._validate_missiles_enabled(client.server)

        self._validate_field_not_none(self._pais, "País")

        if self._pais is None:
            return

        TurnValidator.validate_turn(client, context.game)
        GameStateValidator.validate_game_started(context.game)

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._pais)

        UnitValidator.validate_min_units(
            context.mapa,
            self._pais,
            MISSILE_UNIT_COST,
            (
                f"Se requieren al menos {MISSILE_UNIT_COST} unidades "
                f"para canjear un misil. {self._pais} tiene "
                f"{context.mapa.cantidad_unidades(self._pais)} unidades."
            ),
        )

        for _ in range(MISSILE_UNIT_COST):
            context.mapa.restar_una_unidad(self._pais)

        context.mapa.agregar_misil(self._pais)
        cantidad_misiles = context.mapa.cantidad_misiles(self._pais)

        context.enviar_misil_agregado(self._pais, cantidad_misiles)
        context.enviar_mapa()

        client.transmisor.enviar_sistema(
            f"Misil canjeado en {self._pais}: -{MISSILE_UNIT_COST} unidades, +1 misil. "
            f"Total: {cantidad_misiles} misiles"
        )
