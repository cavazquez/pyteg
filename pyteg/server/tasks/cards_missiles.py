"""Tareas del servidor: tarjetas y misiles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import (
    MIN_UNITS_TO_LEAVE,
    MISSILE_MAX_DISTANCE,
    MISSILE_UNIT_COST,
    SPECIAL_EXCHANGE_UNITS,
)
from pyteg.exception import (
    CountryNotOwnedError,
    InsufficientUnitsError,
    InvalidActionError,
    MissileOutOfRangeError,
    MissilesNotEnabledError,
    MissingFieldError,
    NoMissilesAvailableError,
)
from pyteg.server.juego.validators import (
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitValidator,
    ValidationError,
)
from pyteg.server.tasks.base import LOGGER, IServerTask

if TYPE_CHECKING:
    from pyteg.game_context import GameContext


class ServerTaskSolicitarTarjetas(IServerTask):
    """Tarea para solicitar las tarjetas del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de solicitar tarjetas.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        # No necesita validación de estado específica

    def _execute(self, client: Any, context: GameContext) -> None:
        """Envía las tarjetas del jugador al cliente que las solicita."""
        context.enviar_tarjetas_jugador(client)


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
        # Verificar que el juego haya comenzado
        GameStateValidator.validate_game_started(context.game)

        if context.game is None:
            return

        # Verificar que sea el turno del jugador
        TurnValidator.validate_turn(client, context.game)

        # Verificar que el jugador pueda reclamar tarjeta (conquistó país en este turno)
        if not context.game.puede_reclamar_tarjeta(client):
            msg = "No has conquistado ningún país en este turno"
            raise InvalidActionError(msg)

        # Asignar la tarjeta
        LOGGER.info("Asignando tarjeta a %s por reclamación manual", client.username())
        context.game.dame_una_tarjeta(client)

        # Remover al jugador de la lista de elegibles (solo una tarjeta por turno)
        context.game.reclamar_tarjeta_jugador(client)

        # Enviar tarjetas actualizadas al cliente
        context.enviar_tarjetas_jugador(client)

        # Notificar éxito
        client.transmisor.enviar_sistema("Tarjeta reclamada exitosamente")


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

        # Validar que el país esté especificado
        if self._pais is None:
            msg = "País"
            raise MissingFieldError(msg)

        if context.game is None:
            return

        mapa = context.game.mapa()
        mazo = context.game.mazo()

        # Validar que el jugador posee el país
        if not mapa.jugador_posee_pais(client, self._pais):
            raise CountryNotOwnedError(self._pais)

        # Buscar y remover la tarjeta correspondiente al país
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

        # Realizar el canje especial
        # 1. Remover la tarjeta del jugador
        tarjeta_encontrada.desasignar()
        tarjeta_encontrada.desusar()

        # 2. Agregar unidades al país
        for _ in range(SPECIAL_EXCHANGE_UNITS):
            mapa.agregar_una_unidad(self._pais)

        # 3. Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()

        # 4. Enviar notificación específica del canje especial
        client.transmisor.enviar_canje_especial(self._pais, SPECIAL_EXCHANGE_UNITS)

        # 5. Actualizar tarjetas del jugador
        context.enviar_tarjetas_jugador(client)

        # 6. Notificar éxito
        client.transmisor.enviar_sistema(
            f"Canje especial realizado: +{SPECIAL_EXCHANGE_UNITS} "
            f"unidades en {self._pais}"
        )


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
        # 1. Verificar que los misiles estén habilitados
        self._validate_missiles_enabled(client.server)

        # 2. Validar que el país esté especificado
        self._validate_field_not_none(self._pais, "País")

        # Type narrowing: después de la validación, este valor no es None
        if self._pais is None:
            return  # No debería llegar aquí, pero ayuda a MyPy

        # 3. Validar turno y estado del juego
        TurnValidator.validate_turn(client, context.game)
        GameStateValidator.validate_game_started(context.game)

        # 4. Validar propiedad del país
        CountryOwnershipValidator.validate_ownership(client, context.mapa, self._pais)

        # 5. Validar unidades mínimas para canjear misil
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

        # 6. Restar las unidades del país
        for _ in range(MISSILE_UNIT_COST):
            context.mapa.restar_una_unidad(self._pais)

        # 7. Agregar misil al país
        context.mapa.agregar_misil(self._pais)
        cantidad_misiles = context.mapa.cantidad_misiles(self._pais)

        # 8. Notificar cambios a todos los clientes
        context.enviar_misil_agregado(self._pais, cantidad_misiles)
        # Actualizar el mapa completo para mostrar cambios en unidades
        context.enviar_mapa()

        # 10. Notificar éxito al jugador
        client.transmisor.enviar_sistema(
            f"Misil canjeado en {self._pais}: -{MISSILE_UNIT_COST} unidades, +1 misil. "
            f"Total: {cantidad_misiles} misiles"
        )


class ServerTaskLanzarMisil(IServerTask):
    """Tarea para lanzar un misil desde un país hacia otro."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de lanzar misil.

        Args:
            data: Datos con país de origen y destino del misil.

        """
        super().__init__(data)
        self._pais_origen = data.get("pais_origen")
        self._pais_destino = data.get("pais_destino")
        self._action_name = "lanzar_misil"

    def _execute(self, client: Any, context: GameContext) -> None:
        # Validar que los países estén especificados
        if self._pais_origen is None:
            msg = "País de origen"
            raise MissingFieldError(msg)
        if self._pais_destino is None:
            msg = "País de destino"
            raise MissingFieldError(msg)

        # Validar precondiciones y permisos
        self._validar_lanzamiento_misil(client, context)

        # Calcular distancia y daño
        distancia = context.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )
        dano = context.mapa.calcular_dano_misil(distancia)

        # Aplicar el daño y usar el misil
        for _ in range(dano):
            context.mapa.restar_una_unidad(self._pais_destino)
        context.mapa.usar_misil(self._pais_origen)

        # Notificar resultados
        self._notificar_resultado_misil(client, distancia, dano)

        # Notificar cambios en el mapa
        context.enviar_mapa()

    def _validar_lanzamiento_misil(self, client: Any, context: GameContext) -> None:
        """Valida todas las condiciones para lanzar un misil.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        """
        # Validar configuración y estado del juego
        self._validar_estado_juego(client, context)

        # Validar posesión y disponibilidad
        self._validar_posesion_misil(client, context)

        # Validar distancia y daño
        self._validar_distancia_dano(client, context)

    def _validar_estado_juego(self, client: Any, context: GameContext) -> None:
        """Valida que el juego esté en estado correcto.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Raises:
            MissilesNotEnabledError: Si los misiles no están habilitados.

        """
        if not context.misiles_habilitados():
            raise MissilesNotEnabledError

        GameStateValidator.validate_game_started(context.game)

        if context.game is None:
            return

        TurnValidator.validate_turn(client, context.game)

    def _validar_posesion_misil(self, client: Any, context: GameContext) -> None:
        """Valida posesión de países y disponibilidad de misiles.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Raises:
            MissingFieldError: Si falta país de origen o destino.
            NoMissilesAvailableError: Si no hay misiles disponibles.
            InvalidActionError: Si intenta lanzar a su propio país.

        """
        if self._pais_origen is None or self._pais_destino is None:
            msg = "País de origen o destino"
            raise MissingFieldError(msg)

        CountryOwnershipValidator.validate_ownership(
            client, context.mapa, self._pais_origen
        )

        if context.mapa.cantidad_misiles(self._pais_origen) == 0:
            raise NoMissilesAvailableError(self._pais_origen)

        if context.mapa.ocupado_por(self._pais_destino) == client.userid():
            msg = "No puedes lanzar misiles a tus propios países"
            raise InvalidActionError(msg)

    def _validar_distancia_dano(
        self,
        client: Any,  # noqa: ARG002
        context: GameContext,
    ) -> None:
        """Valida distancia y daño del misil.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Raises:
            MissingFieldError: Si falta país de origen o destino.
            InvalidActionError: Si no hay camino entre países.
            MissileOutOfRangeError: Si el misil está fuera de rango.
            InsufficientUnitsError: Si el ataque dejaría el país sin unidades.

        """
        if self._pais_origen is None or self._pais_destino is None:
            msg = "País de origen o destino"
            raise MissingFieldError(msg)

        distancia = context.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )

        if distancia == -1:
            msg = f"No hay camino entre {self._pais_origen} y {self._pais_destino}"
            raise InvalidActionError(msg)

        if distancia > MISSILE_MAX_DISTANCE:
            raise MissileOutOfRangeError(distancia, MISSILE_MAX_DISTANCE)

        dano = context.mapa.calcular_dano_misil(distancia)
        unidades_destino = context.mapa.cantidad_unidades(self._pais_destino)
        if unidades_destino <= dano:
            raise InsufficientUnitsError(
                self._pais_destino,
                MIN_UNITS_TO_LEAVE + 1,
                unidades_destino,
            )

    def _notificar_resultado_misil(
        self, client: Any, distancia: int, dano: int
    ) -> None:
        """Notifica el resultado del lanzamiento del misil a todos."""
        unidades_restantes = client.server.mapa.cantidad_unidades(self._pais_destino)

        resultado_data = {
            "jugador": client.username(),
            "pais_origen": self._pais_origen,
            "pais_destino": self._pais_destino,
            "distancia": distancia,
            "dano": dano,
            "unidades_restantes": unidades_restantes,
        }

        client.server.enviar_resultado_misil(resultado_data)
        # Actualizar el mapa completo y misiles
        client.server.enviar_mapa()
        cantidad_misiles_origen = client.server.mapa.cantidad_misiles(self._pais_origen)
        client.server.enviar_misil_agregado(self._pais_origen, cantidad_misiles_origen)
