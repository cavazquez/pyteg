"""Módulo para verificación de condiciones de victoria.

Este módulo encapsula la lógica de verificación de condiciones de victoria,
separando esta responsabilidad del Game principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.core.partida.objetivos_secretos import (
    NO_SECRET_OBJECTIVES,
    SecretObjectiveEvaluator,
)
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pyteg.protocols import IClientProtocol
    from pyteg.server.juego.mapa import Mapa


LOGGER = get_logger(__name__)


class VictoryChecker:
    """Verifica las condiciones de victoria del juego.

    Esta clase se encarga de verificar si algún jugador ha cumplido
    las condiciones para ganar la partida, ya sea por países controlados
    o por objetivos secretos.
    """

    def __init__(  # noqa: PLR0913
        self,
        mapa: Mapa,
        paises_para_victoria: int,
        secret_objectives: SecretObjectiveEvaluator = NO_SECRET_OBJECTIVES,
        *,
        color_manager: Any | None = None,
        objetivos_secretos: SecretObjectiveEvaluator | None = None,
        objetivos_secretos_activados: bool | None = None,
        player_order: Callable[[], list[int]] | None = None,
    ) -> None:
        """Inicializa el verificador de victoria.

        Args:
            mapa: Instancia del mapa del juego.
            paises_para_victoria: Cantidad de países necesarios para ganar.
            secret_objectives: Evaluador de objetivos secretos. Usar
                ``NO_SECRET_OBJECTIVES`` cuando la regla está desactivada.
            color_manager: Instancia del gestor de colores.
            objetivos_secretos: Nombre anterior de ``secret_objectives``,
                conservado para compatibilidad con integraciones existentes.
            objetivos_secretos_activados: Compatibilidad con la configuración
                anterior. Cuando es ``False`` se selecciona el objeto nulo.
            player_order: Callback que devuelve el orden actual de turnos.

        """
        self._mapa = mapa
        self._paises_para_victoria = paises_para_victoria
        if objetivos_secretos is not None:
            secret_objectives = objetivos_secretos
        if objetivos_secretos_activados is False:
            secret_objectives = NO_SECRET_OBJECTIVES
        self._secret_objectives = secret_objectives
        self._color_manager = color_manager
        if player_order is not None:
            configurar_orden = getattr(secret_objectives, "set_player_order", None)
            if callable(configurar_orden):
                configurar_orden(player_order)

    def verificar_condicion_victoria(
        self, jugadores: Sequence[IClientProtocol]
    ) -> IClientProtocol | None:
        """Verifica si algún jugador ha ganado la partida.

        Verifica si algún jugador ha ganado controlando el número objetivo
        de países o cumpliendo su objetivo secreto.

        Args:
            jugadores: Lista de jugadores del juego.

        Returns:
            El jugador ganador si existe, None en caso contrario.

        """
        total_paises = len(self._mapa.paises())

        # Si no hay países en el mapa, no puede haber ganador (edge case para tests)
        if total_paises == 0:
            return None

        ganador = self._verificar_objetivos_secretos(jugadores)
        if ganador:
            return ganador

        # Verificar condición de victoria tradicional (por países)
        return self._verificar_victoria_por_paises(jugadores, total_paises)

    def _verificar_objetivos_secretos(
        self, jugadores: Sequence[IClientProtocol]
    ) -> IClientProtocol | None:
        """Verifica si algún jugador cumplió su objetivo secreto.

        Args:
            jugadores: Lista de jugadores del juego.

        Returns:
            El jugador ganador si existe, None en caso contrario.

        """
        if not self._color_manager:
            return None

        for jugador in jugadores:
            jugador_id = int(jugador.userid())
            if self._secret_objectives.verificar_condicion_victoria(
                jugador_id,
                self._mapa,
                self._color_manager,
            ):
                jugador_nombre = (
                    jugador.username() if hasattr(jugador, "username") else str(jugador)
                )
                objetivo = self._secret_objectives.get_objetivo_jugador(jugador_id)
                LOGGER.info(
                    "%s ha ganado cumpliendo su objetivo secreto",
                    jugador_nombre,
                )
                if objetivo:
                    LOGGER.info("Objetivo cumplido: %s", objetivo["descripcion"])
                return jugador

        return None

    def _verificar_victoria_por_paises(
        self, jugadores: Sequence[IClientProtocol], total_paises: int
    ) -> IClientProtocol | None:
        """Verifica si algún jugador ganó por países controlados.

        Args:
            jugadores: Lista de jugadores del juego.
            total_paises: Total de países en el mapa.

        Returns:
            El jugador ganador si existe, None en caso contrario.

        """
        for jugador in jugadores:
            jugador_id = int(jugador.userid())
            jugador_nombre = (
                jugador.username() if hasattr(jugador, "username") else str(jugador)
            )
            paises_controlados = self._mapa.cantidad_de_paises_del_jugador(jugador_id)

            if self._paises_para_victoria == 0:
                objetivo_paises = total_paises
            else:
                objetivo_paises = self._paises_para_victoria

            if paises_controlados >= objetivo_paises:
                if self._paises_para_victoria == 0:
                    LOGGER.info(
                        "%s ha ganado controlando todos los países",
                        jugador_nombre,
                    )
                else:
                    LOGGER.info(
                        "%s ha ganado controlando %s países",
                        jugador_nombre,
                        paises_controlados,
                    )
                return jugador

        return None
