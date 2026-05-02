"""Tarea: lanzar un misil desde un país propio hacia otro."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import MIN_UNITS_TO_LEAVE, MISSILE_MAX_DISTANCE
from pyteg.exceptions import (
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
)
from pyteg.server.tasks.base import IServerTask

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext


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
        if self._pais_origen is None:
            msg = "País de origen"
            raise MissingFieldError(msg)
        if self._pais_destino is None:
            msg = "País de destino"
            raise MissingFieldError(msg)

        self._validar_lanzamiento_misil(client, context)

        distancia = context.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )
        dano = context.mapa.calcular_dano_misil(distancia)

        for _ in range(dano):
            context.mapa.restar_una_unidad(self._pais_destino)
        context.mapa.usar_misil(self._pais_origen)

        self._notificar_resultado_misil(client, distancia, dano)

        context.enviar_mapa()

    def _validar_lanzamiento_misil(self, client: Any, context: GameContext) -> None:
        """Valida todas las condiciones para lanzar un misil.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        """
        self._validar_estado_juego(client, context)

        self._validar_posesion_misil(client, context)

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
            "jugador_id": int(client.userid()),
            "jugador": client.username(),
            "pais_origen": self._pais_origen,
            "pais_destino": self._pais_destino,
            "distancia": distancia,
            "dano": dano,
            "unidades_restantes": unidades_restantes,
        }

        client.server.enviar_resultado_misil(resultado_data)
        client.server.enviar_mapa()
        cantidad_misiles_origen = client.server.mapa.cantidad_misiles(self._pais_origen)
        client.server.enviar_misil_agregado(self._pais_origen, cantidad_misiles_origen)
