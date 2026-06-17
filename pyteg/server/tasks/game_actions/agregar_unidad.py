"""Tarea: agregar unidades a un país propio durante el reparto."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import VALID_UNIT_TYPES
from pyteg.core.turnos.unit_pool import (
    consumir_unidad_reparto,
    unidades_disponibles_en_pais,
)
from pyteg.server.juego.validators import (
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitTypeValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask
from pyteg.server.tasks.types import AgregarUnidadTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskAgregarUnidad(IServerTask[AgregarUnidadTaskData]):
    """Tarea para agregar unidades a un país."""

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

    def __init__(self, data: AgregarUnidadTaskData) -> None:
        """Inicializa la tarea de agregar unidad.

        Args:
            data: Datos con país, tipo de unidad y cantidad.

        """
        super().__init__(data)
        self._pais: str | None = data.get("pais")
        self._tipo_unidad: str | None = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)
        self._action_name = "agregar_unidad"

    def _validate_units_available(
        self, turno_actual: Any, continente_pais: str, cantidad: int
    ) -> None:
        """Valida que haya suficientes unidades para colocar en el país.

        Args:
            turno_actual: Turno actual del juego.
            continente_pais: Continente del país destino.
            cantidad: Cantidad de unidades requeridas.

        Raises:
            ValidationError: Si no hay suficientes unidades disponibles.

        """
        disponibles = unidades_disponibles_en_pais(turno_actual, continente_pais)
        if disponibles < cantidad:
            msg = (
                f"No hay suficientes unidades disponibles para agregar "
                f"{cantidad} unidad(es) en este continente"
            )
            raise ValidationError(msg)

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        self._validate_field_not_none(self._pais, "País")
        self._validate_field_not_none(self._tipo_unidad, "Tipo de unidad")

        if self._pais is None or self._tipo_unidad is None:
            return

        TurnValidator.validate_turn(client, context.game)
        GameStateValidator.validate_game_started(context.game)

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._pais)

        UnitTypeValidator.validate_unit_type(self._tipo_unidad, VALID_UNIT_TYPES)

        if context.game is None:
            return
        turno_actual = context.game.turno_actual()
        continente_pais = context.mapa.continente(self._pais)
        self._validate_units_available(turno_actual, continente_pais, self._cantidad)

        for _ in range(self._cantidad):
            context.mapa.agregar_una_unidad(self._pais)
            consumir_unidad_reparto(turno_actual, continente_pais)

        msg = (
            f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
            f" en {self._pais}"
        )
        LOGGER.info(msg)

        context.enviar_mapa()

        context.enviar_unidades_disponibles()
