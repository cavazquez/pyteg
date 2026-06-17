"""Módulo para coordinar el inicio y configuración de partidas.

Este módulo encapsula la lógica de configuración e inicio de partidas,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import DEFAULT_TURN_SECONDS, VICTORY_ALL_COUNTRIES
from pyteg.core.turnos.timer import TurnoTimer
from pyteg.logger import get_logger
from pyteg.server.juego.game import Game

if TYPE_CHECKING:
    from pyteg.core.cartas.mazo import Mazo
    from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
    from pyteg.server.juego.estado import Estado
    from pyteg.server.juego.mapa import Mapa


LOGGER = get_logger(__name__)


class ServerGameCoordinator:
    """Coordina la configuración e inicio de partidas.

    Esta clase se encarga de toda la lógica relacionada con la configuración
    de parámetros de partida y el inicio de la misma, separando esta
    responsabilidad del Server principal.
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        mapa: Mapa,
        mazo: Mazo,
        objetivos_secretos: ObjetivosSecretos,
        estado: Estado,
        get_clients: Any,
        broadcaster: Any,
        color_manager: Any,
    ) -> None:
        """Inicializa el coordinador de partidas.

        Args:
            mapa: Instancia del mapa del juego.
            mazo: Instancia del mazo de tarjetas.
            objetivos_secretos: Instancia del gestor de objetivos secretos.
            estado: Instancia del estado del servidor.
            get_clients: Función o método que retorna la lista de clientes.
            broadcaster: Instancia del broadcaster de mensajes.
            color_manager: Instancia del gestor de colores.

        """
        self._mapa = mapa
        self._mazo = mazo
        self._objetivos_secretos = objetivos_secretos
        self._estado = estado
        self._get_clients = get_clients
        self._broadcaster = broadcaster
        self._color_manager = color_manager

        # Configuración de partida
        self._segundos_por_turno: int = DEFAULT_TURN_SECONDS
        self._paises_para_victoria: int = VICTORY_ALL_COUNTRIES
        self._objetivos_secretos_activados: bool = False
        self._misiles_habilitados: bool = False

        # Referencia al juego (se crea al iniciar la partida)
        self._game: Game | None = None
        self._turno_timer: TurnoTimer | None = None

    def set_segundos_por_turno(self, segundos: int) -> None:
        """Configura la cantidad de segundos por turno.

        Args:
            segundos: Segundos por turno (> 0).

        """
        if isinstance(segundos, int) and segundos > 0:
            self._segundos_por_turno = segundos

    def set_paises_para_victoria(self, paises: int) -> None:
        """Configura la cantidad de países necesarios para ganar.

        Args:
            paises: Países necesarios para victoria (> 0).

        """
        if isinstance(paises, int) and paises > 0:
            self._paises_para_victoria = paises

    def set_objetivos_secretos(self, *, activados: bool) -> None:
        """Configura si los objetivos secretos están activados.

        Args:
            activados: True si los objetivos secretos están activados.

        """
        self._objetivos_secretos_activados = activados

    def set_misiles_habilitados(self, *, activados: bool) -> None:
        """Configura si los misiles están habilitados.

        Args:
            activados: True si los misiles están habilitados.

        """
        self._misiles_habilitados = activados

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados en esta partida.

        Returns:
            True si los misiles están habilitados.

        """
        return self._misiles_habilitados

    def enviar_configuracion_partida(self) -> None:
        """Envía la configuración de la partida a todos los clientes.

        Este método puede ser llamado para reenviar la configuración
        después de que la partida haya comenzado.
        """
        self._broadcaster.enviar_configuracion_partida(
            self._segundos_por_turno,
            self._paises_para_victoria,
            objetivos_secretos=self._objetivos_secretos_activados,
            misiles_habilitados=self._misiles_habilitados,
        )

    def empezar_partida(self, server: Any) -> Game:
        """Inicia la partida con la configuración actual.

        Args:
            server: Referencia al servidor (para pasar al Game).

        Returns:
            Instancia del juego creado.

        """
        LOGGER.info("Iniciando partida...")

        # Obtener la lista de jugadores
        jugadores = self._get_clients()
        LOGGER.info(
            "Jugadores conectados: %s",
            [j.userid() for j in jugadores],
        )

        # Crear e iniciar el juego, pasando la referencia al servidor
        self._game = Game(
            self._mapa,
            self._mazo,
            jugadores,
            server,
            self._paises_para_victoria,
            objetivos_secretos_activados=self._objetivos_secretos_activados,
        )
        self._game.empezar()

        # Enviar información de los jugadores y sus colores a todos los clientes
        LOGGER.info("Enviando colores asignados a los jugadores...")
        server.enviar_colores_asignados()

        # Enviar el mapa con los países y sus propietarios
        LOGGER.info("Enviando mapa a los jugadores...")
        server.enviar_mapa()

        # Notificar a los clientes que la partida ha comenzado
        LOGGER.info("Notificando a los clientes que la partida ha comenzado...")
        # Cambiar el estado a EmpezarPartida
        self._estado.empezar_partida()
        self._broadcaster.enviar_estado(self._estado.estado_actual())

        # Enviar el número de turno inicial a todos los clientes
        LOGGER.info("Enviando número de turno inicial a los clientes...")
        server.enviar_turno_actual()

        # Enviar la configuración de la partida a todos los clientes
        LOGGER.info("Enviando configuración de la partida a los clientes...")
        server.enviar_configuracion_partida()

        # Asignar y enviar objetivos secretos si están activados
        if self._objetivos_secretos_activados:
            LOGGER.info("Asignando objetivos secretos a los jugadores...")
            self._objetivos_secretos.asignar_objetivos_aleatorios(jugadores)
            server.enviar_objetivos_secretos()

        # Iniciar el temporizador de turnos
        LOGGER.info("Iniciando temporizador de turnos...")
        self._turno_timer = TurnoTimer(
            server, segundos_por_turno=self._segundos_por_turno
        )
        self._turno_timer.start()

        return self._game

    def game(self) -> Game | None:
        """Obtiene la instancia del juego actual.

        Returns:
            Instancia del juego o None si no ha comenzado.

        """
        return self._game

    def turno_timer(self) -> TurnoTimer | None:
        """Obtiene el temporizador de turnos.

        Returns:
            Instancia del temporizador o None si no está iniciado.

        """
        return self._turno_timer
