"""Módulo para verificación de condiciones de victoria.

Este módulo encapsula la lógica de verificación de condiciones de victoria,
separando esta responsabilidad del Game principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
    from pyteg.protocols import IClientProtocol
    from pyteg.server.juego.color import ServerColor
    from pyteg.server.juego.mapa import Mapa


LOGGER = get_logger(__name__)


class VictoryChecker:
    """Verifica las condiciones de victoria del juego.

    Esta clase se encarga de verificar si algún jugador ha cumplido
    las condiciones para ganar la partida, ya sea por países controlados
    o por objetivos secretos.
    """

    def __init__(
        self,
        mapa: Mapa,
        paises_para_victoria: int,
        objetivos_secretos: ObjetivosSecretos | None = None,
        *,
        objetivos_secretos_activados: bool = False,
        color_manager: ServerColor | None = None,
    ) -> None:
        """Inicializa el verificador de victoria.

        Args:
            mapa: Instancia del mapa del juego.
            paises_para_victoria: Cantidad de países necesarios para ganar.
            objetivos_secretos: Instancia del gestor de objetivos secretos.
            objetivos_secretos_activados: Si los objetivos secretos están activados.
            color_manager: Instancia del gestor de colores.

        """
        self._mapa = mapa
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self._objetivos_secretos_activados = objetivos_secretos_activados
        self._color_manager = color_manager

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

        # Verificar objetivos secretos si están activados
        if self._objetivos_secretos_activados and self._objetivos_secretos:
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
        if not self._objetivos_secretos or not self._color_manager:
            return None

        for jugador in jugadores:
            jugador_id = int(jugador.userid())
            if self._objetivos_secretos.verificar_condicion_victoria(
                jugador_id,
                self._mapa._mapa,  # noqa: SLF001
                self._color_manager,
            ):
                jugador_nombre = (
                    jugador.username() if hasattr(jugador, "username") else str(jugador)
                )
                objetivo = self._objetivos_secretos.get_objetivo_jugador(jugador_id)
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
