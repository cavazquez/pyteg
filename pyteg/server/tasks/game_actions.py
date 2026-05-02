"""Tareas del servidor: acciones de juego en mapa (unidades, ataque, turno)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import (
    MIN_UNITS_FOR_ATTACK,
    VALID_UNIT_TYPES,
)
from pyteg.exception import MissingFieldError
from pyteg.server.juego.validators import (
    AdjacencyValidator,
    AttackRestrictionValidator,
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitTypeValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask

if TYPE_CHECKING:
    from pyteg.game_context import GameContext


class ServerTaskAgregarUnidad(IServerTask):
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

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de agregar unidad.

        Args:
            data: Datos con país, tipo de unidad y cantidad.

        """
        super().__init__(data)
        self._pais: str | None = data.get("pais")
        self._tipo_unidad: str | None = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "agregar_unidad"

    def _validate_units_available(self, turno_actual: Any, cantidad: int) -> None:
        """Valida que haya suficientes unidades disponibles.

        Args:
            turno_actual: Turno actual del juego.
            cantidad: Cantidad de unidades requeridas.

        Raises:
            ValidationError: Si no hay suficientes unidades disponibles.

        """
        if (
            not hasattr(turno_actual, "cant_unidades")
            or turno_actual.cant_unidades() < cantidad
        ):
            msg = (
                f"No hay suficientes unidades disponibles para agregar "
                f"{cantidad} unidades"
            )
            raise ValidationError(msg)

    def _execute(self, client: Any, context: GameContext) -> None:
        # Validar que los datos requeridos estén presentes
        self._validate_field_not_none(self._pais, "País")
        self._validate_field_not_none(self._tipo_unidad, "Tipo de unidad")

        # Type narrowing: después de las validaciones, estos valores no son None
        if self._pais is None or self._tipo_unidad is None:
            return  # No debería llegar aquí, pero ayuda a MyPy

        # Validar turno y estado del juego
        TurnValidator.validate_turn(client, context.game)
        GameStateValidator.validate_game_started(context.game)

        # Validar propiedad del país
        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._pais)

        # Validar tipo de unidad
        UnitTypeValidator.validate_unit_type(self._tipo_unidad, VALID_UNIT_TYPES)

        # Verificar que el jugador tenga suficientes unidades disponibles
        if context.game is None:
            return
        turno_actual = context.game.turno_actual()
        self._validate_units_available(turno_actual, self._cantidad)

        # Obtener el turno actual para usar después
        if context.game is None:
            return
        turno_actual = context.game.turno_actual()

        # Agregar la unidad al país
        for _ in range(self._cantidad):
            context.mapa.agregar_una_unidad(self._pais)

            # Restar la unidad de las unidades generales disponibles
            if hasattr(turno_actual, "usar_unidad"):
                turno_actual.usar_unidad()

        msg = (
            f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
            f" en {self._pais}"
        )
        LOGGER.info(msg)

        # Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()

        # Actualizar las unidades disponibles en la interfaz del jugador
        context.enviar_unidades_disponibles()


class ServerTaskMoverUnidad(IServerTask):
    """Tarea para mover unidades entre países."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de mover unidad.

        Args:
            data: Datos con país de origen, destino y cantidad.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
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

    def _execute(self, client: Any, context: GameContext) -> None:
        # Validar que los datos requeridos estén presentes
        self._validate_required_fields()

        # Validar propiedad del país de origen
        # Type narrowing: después de las validaciones, estos valores no son None
        if self._origen is None or self._destino is None:
            return  # No debería llegar aquí, pero ayuda a MyPy

        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._origen)

        # Validar adyacencia (antes de validar propiedad del destino)
        AdjacencyValidator.validate_adjacent(context.mapa, self._origen, self._destino)

        # Validar propiedad del país de destino
        CountryOwnershipValidator.validate_ownership(
            client, context.mapa, self._destino
        )

        # Validar suficientes unidades para mover
        UnitValidator.validate_sufficient_units_to_move(
            context.mapa, self._origen, self._cantidad
        )

        # Mover las unidades
        context.mapa.mover(self._origen, self._destino, self._cantidad)
        LOGGER.info(
            "Se movieron %s unidades de %s a %s",
            self._cantidad,
            self._origen,
            self._destino,
        )

        # Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()


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
        # Validar que los datos requeridos estén presentes
        self._validate_required_fields()

        # Validar cantidad de unidades
        if self._cantidad_unidades is None:
            msg = "Cantidad de unidades"
            raise MissingFieldError(msg)

        # Type narrowing: después de las validaciones, estos valores no son None
        if self._origen is None or self._destino is None:
            return  # No debería llegar aquí, pero ayuda a MyPy

        # Validar estado del juego
        GameStateValidator.validate_game_started(context.game)

        # Validar restricciones de ataque (antes de validar turno)
        if context.game is None:
            return
        AttackRestrictionValidator.validate_not_first_turns(context.game)

        # Validar turno
        TurnValidator.validate_turn(client, context.game)

        # Validar propiedad del país de origen
        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._origen)

        # Validar que el destino NO sea del mismo jugador
        CountryOwnershipValidator.validate_not_own_country(
            client, context.mapa, self._destino
        )

        # Validar adyacencia
        AdjacencyValidator.validate_adjacent(context.mapa, self._origen, self._destino)

        # Validar unidades mínimas para atacar
        UnitValidator.validate_min_units(
            context.mapa,
            self._origen,
            MIN_UNITS_FOR_ATTACK,
            f"Necesitas al menos {MIN_UNITS_FOR_ATTACK} unidades en "
            f"{self._origen} para atacar",
        )

        # Logging del estado antes del ataque
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

        # Realizar el ataque
        if context.game is None:
            return
        info_batalla = context.game.atacar(
            self._origen, self._destino, self._cantidad_unidades
        )

        # Logging del estado después del ataque
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

        # Enviar mapa actualizado a todos los clientes
        context.enviar_mapa()

        # Enviar resultado de la batalla a todos los clientes
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

        # Marcar que el jugador conquistó un país en este turno
        # (para poder reclamar tarjeta)
        if info_batalla["conquistado"]:
            LOGGER.info(
                "%s conquistó %s - puede reclamar tarjeta",
                client.username(),
                self._destino,
            )
            # Marcar al jugador como elegible para reclamar tarjeta
            if context.game is not None:
                context.game.marcar_jugador_puede_reclamar(client)
        # (esto se podría implementar más adelante)


class ServerTaskFinalizarTurno(IServerTask):
    """Tarea para finalizar el turno de un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de finalizar turno.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client: Any, context: GameContext) -> None:
        TurnValidator.validate_turn(client, context.game)

        # Limpiar elegibilidad para reclamar tarjetas del turno anterior
        if context.game is not None:
            context.game.limpiar_elegibilidad_reclamar()

            # Finalizar el turno actual
            context.game.finalizar_turno()

        # Notificar a todos los clientes sobre el cambio de turno
        context.enviar_turno_actual()
        context.enviar_mapa()
