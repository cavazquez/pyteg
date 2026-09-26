"""Módulo para coordinar el inicio y configuración de partidas.

Este módulo encapsula la lógica de configuración e inicio de partidas,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.config import DEFAULT_TURN_SECONDS, VICTORY_ALL_COUNTRIES
from pyteg.core.situaciones.catalog import (
    DEFAULT_SITUATION_RULESET,
    available_situation_rulesets,
    build_situation_deck,
)
from pyteg.core.situaciones.runtime import SituationRuntime
from pyteg.core.turnos.timer import NullTurnTimer, TurnoTimer, TurnTimerProtocol
from pyteg.logger import get_logger
from pyteg.server.juego.game import Game

if TYPE_CHECKING:
    from pyteg.core.cartas.mazo import Mazo
    from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
    from pyteg.core.partida.reglas import ThemeRules
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
        situation_ruleset: str = DEFAULT_SITUATION_RULESET,
        situation_rng: Any = None,
        rules: ThemeRules | None = None,
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
            situation_ruleset: Identificador del ruleset de situaciones.
            situation_rng: Fuente opcional para pruebas reproducibles.
            rules: Perfil de reglas opcional del tema.

        Raises:
            ValueError: Si el ruleset de situaciones no está registrado.

        """
        self._mapa = mapa
        self._mazo = mazo
        self._objetivos_secretos = objetivos_secretos
        self._estado = estado
        self._get_clients = get_clients
        self._broadcaster = broadcaster
        self._color_manager = color_manager
        normalized_situation_ruleset = str(situation_ruleset).strip().lower()
        if normalized_situation_ruleset not in available_situation_rulesets():
            msg = f"Ruleset de situaciones desconocido: {situation_ruleset}"
            raise ValueError(msg)
        self._situation_ruleset = normalized_situation_ruleset
        self._situation_rng = situation_rng
        self._rules = rules

        # Configuración de partida
        self._segundos_por_turno: int = (
            rules.turn_seconds if rules is not None else DEFAULT_TURN_SECONDS
        )
        self._paises_para_victoria: int = (
            rules.lobby_victory_countries
            if rules is not None
            else VICTORY_ALL_COUNTRIES
        )
        self._objetivos_secretos_activados: bool = (
            rules.objectives_enabled if rules is not None else False
        )
        self._misiles_habilitados: bool = (
            rules.missiles_enabled if rules is not None else False
        )

        # Referencia al juego (se crea al iniciar la partida)
        self._game: Game | None = None
        self._turno_timer: TurnTimerProtocol = NullTurnTimer()

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
            paises: Países necesarios para victoria; cero exige todo el mapa.

        """
        if isinstance(paises, int) and paises >= 0:
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

    def set_situation_ruleset(self, ruleset: str) -> None:
        """Selecciona explícitamente el ruleset de situaciones.

        Raises:
            ValueError: Si el ruleset de situaciones no está registrado.

        """
        normalized = str(ruleset).strip().lower()
        if normalized not in available_situation_rulesets():
            msg = f"Ruleset de situaciones desconocido: {ruleset}"
            raise ValueError(msg)
        self._situation_ruleset = normalized

    def situation_ruleset(self) -> str:
        """Devuelve el ruleset de situaciones configurado.

        Returns:
            Identificador del ruleset activo.

        """
        return self._situation_ruleset

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

    def configuracion_partida(self) -> dict[str, Any]:
        """Devuelve la configuración pública vigente de la partida.

        Returns:
            Campos públicos de configuración, sin estado privado.

        """
        return {
            "segundos_por_turno": self._segundos_por_turno,
            "paises_para_victoria": self._paises_para_victoria,
            "objetivos_secretos": self._objetivos_secretos_activados,
            "misiles_habilitados": self._misiles_habilitados,
            "situation_ruleset": self._situation_ruleset,
            "reglas": self._rules.to_public_dict() if self._rules is not None else None,
        }

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
        situation_runtime = SituationRuntime(
            self._mapa,
            build_situation_deck(
                self._situation_ruleset,
                rng=self._situation_rng,
            ),
            dice_rng=self._situation_rng,
        )
        self._game = Game(
            self._mapa,
            self._mazo,
            jugadores,
            server,
            self._paises_para_victoria,
            objetivos_secretos_activados=self._objetivos_secretos_activados,
            situation_runtime=situation_runtime,
            rules=self._rules,
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
            revancha_players = (
                len(jugadores)
                if self._rules is not None and self._rules.theme == "revancha"
                else None
            )
            self._objetivos_secretos.asignar_objetivos_aleatorios(
                jugadores, revancha_players=revancha_players
            )
            server.enviar_objetivos_secretos()

        # Publicar una primera revisión completa cuando la asignación inicial
        # ya terminó, para que todos los clientes arranquen con el mismo estado.
        bump_revision = getattr(server, "bump_state_revision", None)
        enviar_snapshot = getattr(server, "enviar_snapshot", None)
        if callable(bump_revision):
            bump_revision()
        if callable(enviar_snapshot):
            enviar_snapshot()

        # Iniciar el temporizador de turnos
        LOGGER.info("Iniciando temporizador de turnos...")
        self._turno_timer = TurnoTimer(
            server, segundos_por_turno=self._segundos_por_turno
        )
        self._turno_timer.start()

        return self._game

    def finalizar_partida(self) -> bool:
        """Cierra la partida activa y notifica el estado terminal.

        Returns:
            ``True`` si la partida pasó de ``JUGANDO`` a ``Finalizado``.

        """
        if not self._estado.finalizar_partida():
            return False

        self._turno_timer.detener()

        self._broadcaster.enviar_estado(self._estado.estado_actual())
        LOGGER.info("Partida finalizada")
        return True

    def volver_al_lobby(self, server: Any) -> bool:
        """Limpia recursos de partida y conserva las conexiones activas.

        Returns:
            ``True`` si se reabrió la sala.

        """
        if not self._estado.es_finalizado():
            return False
        partida_anterior = self._game
        self.detener()
        jugadores_anteriores = (
            partida_anterior.jugadores() if partida_anterior is not None else []
        )
        preparar_revancha = getattr(server, "preparar_revancha", None)
        if callable(preparar_revancha):
            preparar_revancha(jugadores_anteriores)
        self._mapa.reiniciar()
        self._mazo.reiniciar()
        reiniciar_objetivos = getattr(self._objetivos_secretos, "reiniciar", None)
        if callable(reiniciar_objetivos):
            reiniciar_objetivos()
        self._game = None
        self._turno_timer = NullTurnTimer()
        self._segundos_por_turno = (
            self._rules.turn_seconds
            if self._rules is not None
            else DEFAULT_TURN_SECONDS
        )
        self._paises_para_victoria = (
            self._rules.lobby_victory_countries
            if self._rules is not None
            else VICTORY_ALL_COUNTRIES
        )
        self._objetivos_secretos_activados = (
            self._rules.objectives_enabled if self._rules is not None else False
        )
        self._misiles_habilitados = (
            self._rules.missiles_enabled if self._rules is not None else False
        )
        self._situation_ruleset = (
            self._rules.situation_ruleset
            if self._rules is not None
            else DEFAULT_SITUATION_RULESET
        )
        promover_admin = getattr(server, "promover_administrador", None)
        if callable(promover_admin):
            promover_admin()
        self._estado.volver_al_lobby()
        server.enviar_estado()
        server.bump_state_revision()
        server.enviar_snapshot()
        return True

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
        # Se conserva ``None`` en la API pública antes de comenzar la partida
        # para no romper consumidores existentes; internamente el coordinador
        # siempre opera contra el objeto nulo o el timer real.
        if isinstance(self._turno_timer, NullTurnTimer):
            return None
        return cast("TurnoTimer", self._turno_timer)

    def detener(self) -> None:
        """Detiene y espera el temporizador activo de forma idempotente."""
        self._turno_timer.detener()
        if self._turno_timer.is_alive():
            self._turno_timer.join(timeout=2.0)
