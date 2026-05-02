"""Tarea: mover unidades entre países propios adyacentes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.juego.validators import (
    AdjacencyValidator,
    CountryOwnershipValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask
from pyteg.server.tasks.types import MoverUnidadTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskMoverUnidad(IServerTask[MoverUnidadTaskData]):
    """Tarea para mover unidades entre países."""

    def __init__(self, data: MoverUnidadTaskData) -> None:
        """Inicializa la tarea de mover unidad.

        Args:
            data: Datos con país de origen, destino y cantidad.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad = data.get("cantidad", 1)
        self._action_name = "mover_unidad"

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

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        self._validate_required_fields()

        if self._origen is None or self._destino is None:
            return

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._origen)

        AdjacencyValidator.validate_adjacent(context.mapa, self._origen, self._destino)

        CountryOwnershipValidator.validate_ownership(
            client, context.mapa, self._destino
        )

        UnitValidator.validate_sufficient_units_to_move(
            context.mapa, self._origen, self._cantidad
        )

        context.mapa.mover(self._origen, self._destino, self._cantidad)
        LOGGER.info(
            "Se movieron %s unidades de %s a %s",
            self._cantidad,
            self._origen,
            self._destino,
        )

        context.enviar_mapa()
