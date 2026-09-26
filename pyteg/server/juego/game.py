# ruff: noqa: DOC201, DOC501, TRY003, EM101, EM102

"""Módulo para manejar la lógica del juego en el servidor."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from pyteg.config import (
    DEFAULT_VICTORY_COUNTRIES,
)
from pyteg.core.combate.batalla import Batalla
from pyteg.core.partida.card_manager import CardManager
from pyteg.core.partida.objetivos_secretos import NO_SECRET_OBJECTIVES
from pyteg.core.partida.pactos import PactManager
from pyteg.core.partida.reglas import ThemeRules
from pyteg.core.partida.turn_manager import TurnManager
from pyteg.core.partida.turn_order_rotator import TurnOrderRotator
from pyteg.core.partida.victory_checker import VictoryChecker
from pyteg.core.situaciones.runtime import SituationRuntime
from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from pyteg.exceptions import InvalidActionError, PlayerEliminatedError
from pyteg.logger import get_logger
from pyteg.server.juego.fase import FASE_ACCIONES, FASE_COLOCACION

if TYPE_CHECKING:
    from collections.abc import Sequence
    from random import Random, SystemRandom

    from pyteg.core.cartas.mazo import Mazo
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.protocols import IClientProtocol
    from pyteg.server.app import Server
    from pyteg.server.juego.mapa import Mapa

TurnoType = PrimerTurno | SegundoTurno | SiguientesTurnos

LOGGER = get_logger(__name__)
_REVANCHA_TWO_PLAYERS = 2


class Game:
    """Maneja la lógica principal del juego."""

    def __init__(  # noqa: PLR0913
        self,
        mapa: Mapa,
        mazo: Mazo,
        jugadores: Sequence[IClientProtocol],
        server: Server,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos_activados: bool = False,
        situation_runtime: SituationRuntime | None = None,
        rules: ThemeRules | None = None,
        dice_rng: Random | SystemRandom | None = None,
    ) -> None:
        """Inicializa el juego.

        Args:
            mapa: Mapa del juego.
            mazo: Mazo de tarjetas.
            jugadores: Lista de jugadores.
            server: Referencia al servidor.
            paises_para_victoria: Cantidad de países necesarios para ganar.
            objetivos_secretos_activados: Si la victoria por objetivos está activa.
            situation_runtime: Runtime opcional de cartas de situación.
            rules: Perfil de reglas opcional del tema.
            dice_rng: Fuente opcional de dados para simulaciones reproducibles.

        """
        if paises_para_victoria is None:
            paises_para_victoria = DEFAULT_VICTORY_COUNTRIES
        self._mapa = mapa
        self._start = False
        self._finalizada = False
        self._jugadores: list[IClientProtocol] = list(jugadores)
        self._solo_mode = len(self._jugadores) == 1
        self._revancha_duel = (
            rules is not None
            and rules.theme == "revancha"
            and len(self._jugadores) == _REVANCHA_TWO_PLAYERS
        )
        self._eliminados: set[int] = set()
        self._desconectados: set[int] = set()
        self._reconnect_tokens: dict[int, str] = {}
        self._server = server  # Referencia al servidor para notificar cambios
        self._paises_para_victoria = paises_para_victoria
        self._rules = rules
        self._dice_rng = dice_rng
        self._pact_manager = PactManager(mapa)
        self._fase = FASE_COLOCACION
        self._situation_runtime = (
            situation_runtime
            if situation_runtime is not None
            else SituationRuntime.none(mapa)
        )

        # Inicializar gestor de turnos
        self._turn_manager = TurnManager(
            mapa,
            reinforcement_policy=self._situation_runtime,
            rules=rules,
        )
        self._turn_order_rotator = TurnOrderRotator(
            self._turn_manager.lista_jugadores_orden_turno
        )

        # Inicializar gestor de tarjetas
        self._card_manager = CardManager(mazo, self._turn_manager, rules=rules)

        # Inicializar verificador de victoria
        secret_objectives = NO_SECRET_OBJECTIVES
        if objetivos_secretos_activados:
            configured_objectives = getattr(
                server, "objetivos_secretos", NO_SECRET_OBJECTIVES
            )
            if configured_objectives is not None:
                secret_objectives = configured_objectives

        self._victory_checker = VictoryChecker(
            mapa,
            paises_para_victoria,
            secret_objectives=secret_objectives,
            # El servidor expone tanto los clientes históricos como su color;
            # pasar ese contexto permite resolver objetivos de destrucción y
            # relativos incluso cuando el administrador de colores sólo
            # conoce los colores disponibles.
            color_manager=server,
            player_order=self.lista_jugadores_orden_turno,
        )

    def empezar(self) -> None:
        """Inicia el juego asignando países y creando los primeros turnos."""
        self._situation_runtime.reset()
        self._pact_manager.reiniciar()
        jugadores = self.lista_jugadores()
        jugadores_userids = [int(j.userid()) for j in jugadores]
        self._mapa.asignar_paises(jugadores_userids)
        self._desconectados.clear()
        self._eliminados = {
            jugador_id
            for jugador_id in jugadores_userids
            if not self._mapa.tiene_paises(jugador_id)
        }
        self._reconnect_tokens = {}
        for jugador in jugadores:
            token_getter = getattr(jugador, "reconnect_token", None)
            token = token_getter() if callable(token_getter) else None
            if isinstance(token, str) and token:
                self._reconnect_tokens[int(jugador.userid())] = token
        jugadores_activos = self.jugadores_activos()
        jugadores_activos_ids = [int(j.userid()) for j in jugadores_activos]
        self._turn_manager.inicializar_turnos(jugadores_activos_ids)
        self._card_manager.inicializar_canjes(jugadores_activos_ids)
        self._start = True
        self._actualizar_fase()

    def empezo(self) -> bool:
        """Verifica si el juego ha comenzado.

        Returns:
            True si el juego ha comenzado, False en caso contrario.

        """
        return self._start

    def mazo(self) -> Mazo:
        """Obtiene el mazo de tarjetas.

        Returns:
            El mazo de tarjetas.

        """
        return self._card_manager.mazo()

    def dame_una_tarjeta(self, jugador: IClientProtocol) -> None:
        """Asigna una tarjeta a un jugador. Si tiene 5, fuerza un canje.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        self._validar_jugador_activo(jugador)
        self._card_manager.dame_una_tarjeta(jugador)

    def turnos(self) -> list[TurnoType]:
        """Obtiene la lista de turnos.

        Returns:
            Lista de turnos.

        """
        return self._turn_manager.turnos()

    def turno_actual(self) -> TurnoType:
        """Obtiene el turno actual.

        Returns:
            El turno actual.

        """
        return self._turn_manager.turno_actual()

    def id_turno_actual(self) -> int:
        """Obtiene el índice del turno actual.

        Returns:
            Índice del turno actual.

        """
        return self._turn_manager.id_turno_actual()

    def num_ronda(self) -> int:
        """Obtiene el número de ronda actual.

        Returns:
            Número de ronda.

        """
        return self._turn_manager.num_ronda()

    def rondas_sin_ataque(self) -> int:
        """Devuelve cuántas rondas iniciales son sólo de incorporación."""
        return 1 if self._revancha_duel else self.reglas().first_turns_no_attack

    def fase_actual(self) -> str:
        """Devuelve la fase del turno vigente.

        Returns:
            ``colocacion`` o ``acciones``.

        """
        return self._fase

    def reglas(self) -> ThemeRules:
        """Devuelve las reglas activas para validadores y tareas.

        Returns:
            Perfil de reglas de la partida.

        """
        return self._rules if self._rules is not None else ThemeRules.defaults()

    def situacion_actual(self) -> dict[str, str | int | None]:
        """Devuelve la carta de situación activa para snapshots públicos.

        Returns:
            Payload serializable de la carta activa.

        """
        return self._situation_runtime.public_snapshot()

    def validar_accion_situacion(
        self,
        jugador: IClientProtocol,
        accion: str,
    ) -> None:
        """Valida una acción contra la carta activa."""
        color = jugador.color_actual()
        color_key = color.to_hex().lower() if color is not None else None
        self._situation_runtime.validate_action(
            int(jugador.userid()), accion, color_key
        )

    def validar_ataque_situacion(self, origen: str, destino: str) -> None:
        """Valida fronteras abiertas/cerradas de la carta activa."""
        self._situation_runtime.validate_attack(origen, destino)

    def refuerzos_pendientes(self) -> int:
        """Cantidad de refuerzos que el jugador actual aún puede colocar.

        Returns:
            Suma de unidades de colocación pendientes.

        """
        if not self._start:
            return 0
        turno = self._turn_manager.turno_actual()
        unidades_por_tipo = turno.unidades_por_tipo()
        return sum(max(0, int(cantidad)) for cantidad in unidades_por_tipo.values())

    def _actualizar_fase(self) -> None:
        """Sincroniza la fase con los refuerzos del turno actual."""
        self._fase = (
            FASE_COLOCACION if self.refuerzos_pendientes() > 0 else FASE_ACCIONES
        )

    def cant_canjes(self, jugador: IClientProtocol | int) -> int:
        """Obtiene la cantidad de canjes realizados por un jugador.

        Args:
            jugador: Cliente o userid (int) del jugador.

        Returns:
            Cantidad de canjes realizados.

        """
        return self._card_manager.cant_canjes(jugador)

    def canjear(
        self, jugador: IClientProtocol | int, tarjetas: list[TarjetaDePais]
    ) -> None:
        """Realiza un canje de tarjetas por unidades.

        Args:
            jugador: Cliente o userid (int) del jugador.
            tarjetas: Lista de tarjetas a canjear.

        """
        self._validar_jugador_activo(jugador)
        self._card_manager.canjear(jugador, tarjetas)

    def puede_canjear_tarjetas(self, jugador: IClientProtocol | int) -> bool:
        """Indica si el jugador conserva su canje de la vuelta.

        Returns:
            ``True`` si todavía no canjeó en el turno vigente.

        """
        return self._card_manager.puede_canjear_en_turno(jugador)

    def cant_jugadores(self) -> int:
        """Obtiene la cantidad de jugadores.

        Returns:
            Cantidad de jugadores.

        """
        return len(self.jugadores_activos())

    def mapa(self) -> Mapa:
        """Obtiene el mapa del juego.

        Returns:
            El mapa del juego.

        """
        return self._mapa

    def pactos(self) -> PactManager:
        """Devuelve el gestor autoritativo de pactos de la partida."""
        return self._pact_manager

    def pactos_publicos(self) -> dict[str, object]:
        """Devuelve pactos y bloqueos visibles para todos los clientes."""
        return self._pact_manager.public_snapshot()

    def validar_pacto_ataque(
        self,
        jugador: IClientProtocol | int,
        origen: str,
        destino: str,
        defensor: int | None = None,
    ) -> None:
        """Rechaza ataques o misiles prohibidos por pactos vigentes."""
        jugador_id = int(jugador if isinstance(jugador, int) else jugador.userid())
        if defensor is None:
            defensor = self._mapa.ocupado_por(destino)
        if not self._pact_manager.puede_atacar(
            jugador_id, defensor, origen, destino, self.num_ronda()
        ):
            raise InvalidActionError("Un pacto público impide atacar ese objetivo")

    def validar_refuerzo(self, jugador: IClientProtocol | int, pais: str) -> None:
        """Aplica la excepción oficial del único país frente a un bloqueo."""
        jugador_id = int(jugador if isinstance(jugador, int) else jugador.userid())
        if self._pact_manager.esta_bloqueado(pais, jugador_id):
            raise InvalidActionError(
                f"{pais} está bloqueado y no puede recibir refuerzos esta vuelta"
            )

    def finalizar_turno(self) -> None:
        """Finaliza el turno actual y avanza al siguiente."""
        if self._finalizada:
            return

        jugadores_activos = self.jugadores_activos()
        if not self._solo_mode and len(jugadores_activos) == 1:
            self._finalizar_partida(jugadores_activos[0])
            return

        ronda_completada = self._turn_manager.avanzar_turno()
        num = self._turn_manager.id_turno_actual()
        cant_jugadores = self.cant_jugadores()

        if num >= cant_jugadores or ronda_completada:
            self._iniciar_nueva_ronda(jugadores_activos)
        else:
            self._actualizar_fase()

    def _iniciar_nueva_ronda(
        self, jugadores_activos: Sequence[IClientProtocol]
    ) -> None:
        """Coordina las reglas y notificaciones de una ronda nueva."""
        # En una partida solitaria todos los países son propios desde el inicio;
        # evaluar la victoria terminaría la práctica en la primera ronda.
        ganador = (
            None
            if self._solo_mode
            else self._victory_checker.verificar_condicion_victoria(jugadores_activos)
        )
        if ganador:
            self._finalizar_partida(ganador)
            return

        jugadores_por_id = {int(j.userid()): j for j in jugadores_activos}
        jugadores_userids = self._turn_order_rotator.rotar(
            list(jugadores_por_id),
        )
        turnos_actuales = self._turn_manager.turnos()
        es_segundo_turno = (
            bool(turnos_actuales)
            and isinstance(turnos_actuales[0], PrimerTurno)
            and not self._revancha_duel
        )
        self._turn_manager.iniciar_nueva_ronda(
            jugadores_userids, es_segundo_turno=es_segundo_turno
        )
        self._pact_manager.expirar(self.num_ronda())
        self._situation_runtime.begin_round(
            self.num_ronda(),
            jugadores_userids,
            {
                jugador_id: self._color_key(jugadores_por_id[jugador_id])
                for jugador_id in jugadores_userids
            },
        )
        self._actualizar_fase()

        # Notificar al servidor que se completó una ronda para que actualice los
        # colores, la lista de jugadores y el turno anunciado.
        self._server.enviar_colores_asignados()

    def _finalizar_partida(self, ganador: IClientProtocol) -> None:
        """Cierra el juego y anuncia al ganador una única vez."""
        if self._finalizada or not self._server.finalizar_partida():
            return

        self._finalizada = True
        self._start = False
        ganador_id = int(ganador.userid())
        ganador_nombre = (
            ganador.username() if hasattr(ganador, "username") else str(ganador)
        )
        self._server.enviar_victoria(ganador_id, ganador_nombre)

    def jugadores(self) -> list[IClientProtocol]:
        """Obtiene la lista de jugadores.

        Returns:
            Lista de jugadores.

        """
        return self._jugadores

    def lista_jugadores(self) -> list[IClientProtocol]:
        """Obtiene la lista de jugadores.

        Returns:
            Lista de jugadores.

        """
        return self.jugadores()

    def jugadores_activos(self) -> list[IClientProtocol]:
        """Devuelve participantes que siguen jugando y tienen conexión.

        La lista histórica de participantes se conserva para nombres, chat,
        colores y ocupación del mapa. Los turnos, refuerzos y condición de
        victoria usan sólo este subconjunto.

        Returns:
            Jugadores que no fueron eliminados.

        """
        return [
            jugador
            for jugador in self._jugadores
            if not self.jugador_esta_eliminado(jugador)
            and not self.jugador_esta_desconectado(jugador)
        ]

    def desconectar_jugador(self, jugador: IClientProtocol | int) -> bool:
        """Retira una conexión de los turnos sin borrar su identidad ni países.

        Una desconexión durante una partida no equivale a perder el último
        territorio. El jugador queda en el historial para conservar nombres,
        colores y ocupación del mapa, pero deja de recibir turnos y no impide
        que los jugadores conectados continúen la partida.

        Returns:
            ``True`` cuando la desconexión cambió el estado del juego.

        """
        jugador_id = int(jugador) if isinstance(jugador, int) else int(jugador.userid())
        if (
            jugador_id in self._desconectados
            or jugador_id in self._eliminados
            or not any(int(item.userid()) == jugador_id for item in self._jugadores)
        ):
            return False

        self._desconectados.add(jugador_id)
        self._turn_manager.eliminar_jugador(jugador_id)
        if self._turn_manager.turnos():
            self._actualizar_fase()
        jugadores_activos = self.jugadores_activos()
        if self._solo_mode and not jugadores_activos:
            # Sin rival ni conexión no queda un turno que anunciar. Cerrar la
            # práctica permite que el servidor reabra el lobby vacío. El
            # snapshot del cierre se crea antes de retornar, por lo que el
            # juego debe dejar de exponer su turno ya eliminado.
            self._start = False
            if self._server.finalizar_partida():
                self._finalizada = True
            else:
                self._start = True
            return True
        if not self._solo_mode and len(jugadores_activos) == 1:
            self._finalizar_partida(jugadores_activos[0])
        elif self._turn_manager.ronda_completada():
            self._iniciar_nueva_ronda(jugadores_activos)
        return True

    def puede_reconectar(self, jugador_id: int, token: str) -> bool:
        """Valida una sesión desconectada sin cambiar todavía el estado.

        Returns:
            ``True`` si el jugador sigue recuperable y el token coincide.

        """
        return (
            self.empezo()
            and int(jugador_id) in self._desconectados
            and int(jugador_id) not in self._eliminados
            and self.token_de_sesion_valido(jugador_id, token)
        )

    def token_de_sesion_valido(self, jugador_id: int, token: str) -> bool:
        """Comprueba el token de una identidad sin cambiar el estado de juego.

        Returns:
            ``True`` cuando el token corresponde a la identidad histórica.

        """
        esperado = self._reconnect_tokens.get(int(jugador_id))
        return isinstance(esperado, str) and secrets.compare_digest(esperado, token)

    def reconectar_jugador(
        self, jugador_id: int, client: IClientProtocol, token: str
    ) -> bool:
        """Reemplaza el cliente histórico por una conexión autenticada.

        El turno se agrega al final de la ronda vigente. De ese modo la nueva
        conexión no repite el turno actual ni desplaza el índice que ya está en
        ejecución.

        Returns:
            ``True`` si la identidad fue reemplazada y su turno reintegrado.

        """
        jugador_id = int(jugador_id)
        if not self.puede_reconectar(jugador_id, token):
            return False

        indice = next(
            (
                indice
                for indice, jugador in enumerate(self._jugadores)
                if int(jugador.userid()) == jugador_id
            ),
            None,
        )
        if indice is None:
            return False
        if not self._turn_manager.reintegrar_jugador(jugador_id):
            return False

        anterior = self._jugadores[indice]
        color = anterior.color_actual()
        client.reasignar_userid(jugador_id)
        client.set_reconnect_token(token)
        client.set_username(anterior.username())
        client.asignar_color(color)
        self._jugadores[indice] = client
        self._desconectados.remove(jugador_id)
        return True

    def jugador_esta_desconectado(self, jugador: IClientProtocol | int) -> bool:
        """Indica si el jugador perdió su conexión durante la partida.

        Returns:
            ``True`` si el jugador quedó desconectado.

        """
        jugador_id = int(jugador) if isinstance(jugador, int) else int(jugador.userid())
        return jugador_id in self._desconectados

    def jugador_esta_eliminado(self, jugador: IClientProtocol | int) -> bool:
        """Indica si el jugador perdió su último país en esta partida.

        Args:
            jugador: Cliente o ``userid`` a consultar.

        Returns:
            ``True`` cuando el jugador ya no puede recibir turnos ni acciones.

        """
        jugador_id = int(jugador) if isinstance(jugador, int) else int(jugador.userid())
        return jugador_id in self._eliminados

    def lista_jugadores_orden_turno(self) -> list[int]:
        """Devuelve la lista de userids en el orden actual de los turnos.

        Returns:
            Lista de userids (int) en el orden de los turnos.

        """
        return self._turn_manager.lista_jugadores_orden_turno(self.jugadores_activos())

    def atacar(  # noqa: PLR0912, PLR0914, PLR0915, D417
        self,
        pais_atacante: str,
        pais_defensor: str,
        cantidad_unidades: int | None = None,
        jugador_atacante: int | None = None,
        jugador_defensor: int | None = None,
    ) -> dict[str, Any]:
        """Realiza un ataque entre dos países.

        Args:
            pais_atacante (str): País que inicia el ataque
            pais_defensor (str): País que recibe el ataque
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.

        Returns:
            Diccionario con el resultado del ataque.

        """
        mapa = self.mapa()
        # Un ataque desde/hacia un condominio debe indicar qué color aporta
        # las unidades. El camino histórico sigue usando el dueño exclusivo.
        atacante_id = jugador_atacante or mapa.ocupado_por(pais_atacante)
        defensor_id = jugador_defensor or mapa.ocupado_por(pais_defensor)
        if atacante_id is None or defensor_id is None:
            raise InvalidActionError("El ataque necesita atacante y defensor válidos")
        unidades_atacante = (
            mapa.cantidad_unidades_jugador(pais_atacante, atacante_id)
            if mapa.es_condominio(pais_atacante)
            else mapa.cantidad_unidades(pais_atacante)
        )
        unidades_defensor = (
            mapa.cantidad_unidades_jugador(pais_defensor, defensor_id)
            if mapa.es_condominio(pais_defensor)
            else mapa.cantidad_unidades(pais_defensor)
        )

        # Calcular cuántos dados usar
        if cantidad_unidades is not None:
            max_dice = self._rules.attack_dice_max if self._rules else 3
            cantidad_unidades = max(1, min(max_dice, cantidad_unidades))
            # Validar que no exceda las unidades disponibles (menos 1 que debe quedar)
            max_unidades_disponibles = unidades_atacante - 1
            cantidad_unidades = min(cantidad_unidades, max_unidades_disponibles)
            dados_atacante_count = cantidad_unidades
        else:
            dados_atacante_count = Batalla.calcular_cant_dados_atacante(
                unidades_atacante
            )

        dados_atacante_count = self._situation_runtime.attack_dice(dados_atacante_count)
        # Una carta puede añadir dados, pero nunca puede permitir usar más
        # unidades de las que el país tiene disponibles para el combate.
        dados_atacante_count = min(
            dados_atacante_count,
            max(self._rules.attack_dice_max if self._rules else 3, 4),
            max(unidades_atacante - 1, 0),
        )
        max_defense_dice = self._rules.defense_dice_max if self._rules else 2
        dados_defensor_base = min(
            Batalla.calcular_cant_dados_defensor(unidades_defensor), max_defense_dice
        )
        dados_defensor_count = self._situation_runtime.defense_dice(dados_defensor_base)
        dados_defensor_count = min(
            dados_defensor_count,
            max(max_defense_dice, 4),
            max(unidades_defensor, 0),
        )

        # Generar dados aleatorios
        dados_atacante = sorted(
            [self._tirar_dado() for _ in range(dados_atacante_count)],
            reverse=True,
        )
        dados_defensor = sorted(
            [self._tirar_dado() for _ in range(dados_defensor_count)],
            reverse=True,
        )

        # Resolver nombres solo para presentación (chat / log)
        atacante_nombre = self._username_de(atacante_id)
        defensor_nombre = self._username_de(defensor_id)

        LOGGER.debug("Dados atacante (%s): %s", atacante_nombre, dados_atacante)
        LOGGER.debug("Dados defensor (%s): %s", defensor_nombre, dados_defensor)

        # Batalla.ataquen identifica al perdedor por el mismo valor que se le
        # pasa como atacante/defensor, así que pasamos los userids canónicos.
        resultado = Batalla.ataquen(
            str(atacante_id), str(defensor_id), dados_atacante, dados_defensor
        )

        LOGGER.debug("Resultado batalla: %s", resultado)
        LOGGER.debug("Pérdidas: %s", resultado["restar"])

        for perdedor in resultado["restar"]:
            if perdedor == str(atacante_id):
                LOGGER.debug(
                    "Restando 1 unidad a %s en %s", atacante_nombre, pais_atacante
                )
                mapa.restar_unidad_jugador(pais_atacante, int(atacante_id))
            else:
                LOGGER.debug(
                    "Restando 1 unidad a %s en %s", defensor_nombre, pais_defensor
                )
                mapa.restar_unidad_jugador(
                    pais_defensor,
                    int(defensor_id),
                    normalizar=not mapa.es_condominio(pais_defensor),
                )

        conquistado = False
        unidades_defensor_post_batalla = (
            mapa.cantidad_unidades_jugador(pais_defensor, int(defensor_id))
            if mapa.es_condominio(pais_defensor)
            else mapa.cantidad_unidades(pais_defensor)
        )
        LOGGER.debug(
            "Unidades en %s después de batalla: %s",
            pais_defensor,
            unidades_defensor_post_batalla,
        )

        if unidades_defensor_post_batalla == 0:
            pacto_agresion = self._pact_manager.aggression_for_conquest(
                int(atacante_id), int(defensor_id), pais_defensor, self.num_ronda()
            )
            LOGGER.info("Asignando %s a %s", pais_defensor, atacante_nombre)
            LOGGER.debug("Moviendo 1 unidad de %s a %s", pais_atacante, pais_defensor)
            mapa.restar_unidad_jugador(pais_atacante, int(atacante_id))
            if mapa.es_condominio(pais_defensor):
                mapa.conquistar_condominio(
                    pais_defensor,
                    int(atacante_id),
                    int(defensor_id),
                    unidades=1,
                )
            else:
                mapa.asignar_pais(int(atacante_id), pais_defensor)
                mapa.agregar_una_unidad(pais_defensor)
            conquistado = True

            if pacto_agresion is not None and not mapa.es_condominio(pais_defensor):
                # El país recién conquistado conserva la contribución de ambos
                # aliados. Se toma una unidad del primer país limítrofe del
                # aliado que todavía puede dejar una guarnición.
                aliado = next(
                    jugador
                    for jugador in pacto_agresion.jugadores
                    if jugador != int(atacante_id)
                )
                origen_aliado = next(
                    (
                        pais
                        for pais in mapa.paises()
                        if mapa.jugador_posee_pais(aliado, pais)
                        and pais_defensor in mapa.obtener_paises_adyacentes(pais)
                        and mapa.cantidad_unidades_jugador(pais, aliado) > 1
                    ),
                    None,
                )
                if origen_aliado is not None:
                    mapa.restar_unidad_jugador(origen_aliado, aliado)
                    mapa.agregar_una_unidad(pais_defensor)
                    self._pact_manager.invalidar_por_conquista(pais_defensor)
                    # La ficha del atacante ya quedó en el país; la segunda
                    # ficha proviene del aliado recién trasladado.
                    mapa.crear_condominio(
                        pais_defensor,
                        {int(atacante_id): 1, aliado: 1},
                    )
                    self._pact_manager.registrar_condominio(
                        pais_defensor,
                        (int(atacante_id), aliado),
                        self.num_ronda(),
                    )
                else:
                    self._pact_manager.invalidar_por_conquista(pais_defensor)
            else:
                self._pact_manager.invalidar_por_conquista(pais_defensor)

            self._card_manager.devolver_continentes_perdidos(self._mapa)
            if defensor_id is not None and not mapa.tiene_paises(defensor_id):
                self._eliminar_jugador(defensor_id, atacante_id)

            LOGGER.info("%s ha conquistado %s", atacante_nombre, pais_defensor)
        else:
            LOGGER.debug(
                "El ataque de %s a %s fue repelido",
                atacante_nombre,
                pais_defensor,
            )

        LOGGER.debug(
            "Ataque: %s vs %s | dados atacante=%s defensor=%s | resultado=%s",
            atacante_nombre,
            defensor_nombre,
            dados_atacante,
            dados_defensor,
            resultado,
        )

        return {
            "origen": pais_atacante,
            "destino": pais_defensor,
            "atacante_id": atacante_id,
            "defensor_id": defensor_id,
            "atacante": atacante_nombre,
            "defensor": defensor_nombre,
            "dados_atacante": dados_atacante,
            "dados_defensor": dados_defensor,
            "resultado": resultado,
            "conquistado": conquistado,
        }

    def _tirar_dado(self) -> int:
        """Tira un dado usando la fuente inyectada o entropía del sistema.

        Returns:
            Resultado entre uno y seis.

        """
        if self._dice_rng is not None:
            return self._dice_rng.randint(1, 6)
        return secrets.randbelow(6) + 1

    def _eliminar_jugador(self, eliminado_id: int, conquistador_id: int) -> bool:
        """Registra una eliminación y sincroniza el estado con los clientes.

        La operación es idempotente: la marca en ``_eliminados`` se escribe antes
        de transferir tarjetas, por lo que una repetición no puede entregar
        tarjetas ni publicar una segunda eliminación.

        Args:
            eliminado_id: Jugador que acaba de perder su último país.
            conquistador_id: Jugador que conquistó ese país.

        Returns:
            ``True`` si se registró una eliminación nueva.

        """
        if eliminado_id in self._eliminados or self._mapa.tiene_paises(eliminado_id):
            return False

        self._eliminados.add(eliminado_id)
        self._turn_manager.eliminar_jugador(eliminado_id)
        registrar_sucesion = getattr(self._server, "administrador_eliminado", None)
        if callable(registrar_sucesion):
            registrar_sucesion(eliminado_id)
        tarjetas_transferidas = self._card_manager.transferir_tarjetas_al_conquistador(
            eliminado_id, conquistador_id
        )
        eliminado_nombre = self._username_de(eliminado_id)
        conquistador_nombre = self._username_de(conquistador_id)
        LOGGER.info(
            "Jugador eliminado: %s; %s recibió %s tarjetas",
            eliminado_nombre,
            conquistador_nombre,
            tarjetas_transferidas,
        )
        self._server.enviar_sistema(f"{eliminado_nombre} fue eliminado de la partida.")
        self._server.enviar_colores_asignados()

        jugadores_activos = self.jugadores_activos()
        if not self._solo_mode and len(jugadores_activos) == 1:
            self._finalizar_partida(jugadores_activos[0])

        return True

    def _validar_jugador_activo(self, jugador: IClientProtocol | int) -> None:
        """Rechaza recompensas y canjes solicitados por jugadores eliminados.

        Raises:
            PlayerEliminatedError: Si el jugador ya perdió su último país.

        """
        if self.jugador_esta_eliminado(jugador) or self.jugador_esta_desconectado(
            jugador
        ):
            raise PlayerEliminatedError

    def _username_de(self, userid: int | None) -> str:
        """Resuelve el username de un userid usando los jugadores conectados.

        Args:
            userid: userid (int) del jugador, o None si el país no tiene dueño.

        Returns:
            Nombre del jugador para presentación, o cadena vacía si no se resuelve.

        """
        if userid is None:
            return ""
        for j in self.lista_jugadores():
            if int(j.userid()) == int(userid):
                return j.username() if hasattr(j, "username") else str(j)
        return ""

    @staticmethod
    def _color_key(jugador: IClientProtocol) -> str | None:
        """Normaliza el color de un jugador para las reglas de situación.

        Returns:
            Color hexadecimal normalizado o ``None``.

        """
        color = jugador.color_actual()
        if color is None:
            return None
        to_hex = getattr(color, "to_hex", None)
        if not callable(to_hex):
            return None
        return str(to_hex()).lower()

    def marcar_jugador_puede_reclamar(
        self,
        jugador: IClientProtocol,
        pais_conquistado: str | None = None,
    ) -> None:
        """Marca a un jugador como elegible para reclamar tarjeta.

        Args:
            jugador: Jugador a marcar como elegible.
            pais_conquistado: País recién conquistado, si corresponde.

        """
        self._validar_jugador_activo(jugador)
        continentes: tuple[str, ...] = ()
        if pais_conquistado is not None:
            continente = self._mapa.continente(pais_conquistado)
            if self._mapa.jugador_controla_continente(
                int(jugador.userid()), continente
            ):
                continentes = (continente,)
        self._card_manager.marcar_jugador_puede_reclamar(jugador, continentes)

    def puede_reclamar_tarjeta(self, jugador: IClientProtocol) -> bool:
        """Verifica si un jugador puede reclamar tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si el jugador puede reclamar tarjeta, False en caso contrario.

        """
        return (
            not self.jugador_esta_eliminado(jugador)
            and self._situation_runtime.can_claim_country_card(int(jugador.userid()))
            and self._card_manager.puede_reclamar_tarjeta(jugador)
        )

    def reclamar_tarjeta_jugador(self, jugador: IClientProtocol) -> None:
        """Remueve al jugador de la lista de elegibles tras reclamar.

        Args:
            jugador: Jugador que reclamó la tarjeta.

        """
        self._validar_jugador_activo(jugador)
        self._card_manager.reclamar_tarjeta_jugador(jugador)

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas (al finalizar turno)."""
        self._card_manager.limpiar_elegibilidad_reclamar()
