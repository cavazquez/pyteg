"""Módulo para manejar la lógica del juego en el servidor."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from pyteg.batalla import Batalla
from pyteg.config import (
    DEFAULT_VICTORY_COUNTRIES,
)
from pyteg.game_card_manager import CardManager
from pyteg.game_turn_manager import TurnManager
from pyteg.game_victory_checker import VictoryChecker
from pyteg.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos

if TYPE_CHECKING:
    from pyteg.mazo import Mazo
    from pyteg.server.app import Server
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.mapa import Mapa
    from pyteg.tarjeta_de_pais import TarjetaDePais

TurnoType = PrimerTurno | SegundoTurno | SiguientesTurnos


class Game:
    """Maneja la lógica principal del juego."""

    def __init__(
        self,
        mapa: Mapa,
        mazo: Mazo,
        jugadores: list[Client],
        server: Server,
        paises_para_victoria: int | None = None,
    ) -> None:
        """Inicializa el juego.

        Args:
            mapa: Mapa del juego.
            mazo: Mazo de tarjetas.
            jugadores: Lista de jugadores.
            server: Referencia al servidor.
            paises_para_victoria: Cantidad de países necesarios para ganar.

        """
        if paises_para_victoria is None:
            paises_para_victoria = DEFAULT_VICTORY_COUNTRIES
        self._mapa = mapa
        self._start = False
        self._jugadores = jugadores
        self._server = server  # Referencia al servidor para notificar cambios
        self._paises_para_victoria = paises_para_victoria

        # Inicializar gestor de turnos
        self._turn_manager = TurnManager(mapa)

        # Inicializar gestor de tarjetas
        self._card_manager = CardManager(mazo, self._turn_manager)

        # Inicializar verificador de victoria
        objetivos_secretos_activados = (
            hasattr(server, "_objetivos_secretos") and server._objetivos_secretos  # noqa: SLF001
        )
        self._victory_checker = VictoryChecker(
            mapa,
            paises_para_victoria,
            getattr(server, "objetivos_secretos", None),
            objetivos_secretos_activados=objetivos_secretos_activados,
            color_manager=getattr(server, "color", None),
        )

    def empezar(self) -> None:
        """Inicia el juego asignando países y creando los primeros turnos."""
        jugadores = self.lista_jugadores()
        # Manejar tanto objetos Client como strings (para tests)
        jugadores_nombres = [
            j.username() if hasattr(j, "username") else str(j) for j in jugadores
        ]
        self._turn_manager.inicializar_turnos(jugadores_nombres)
        self._mapa.asignar_paises(jugadores_nombres)
        self._card_manager.inicializar_canjes(jugadores_nombres)
        self._start = True

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

    def dame_una_tarjeta(self, jugador: Client) -> None:
        """Asigna una tarjeta a un jugador. Si tiene 5, fuerza un canje.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
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

    def cant_canjes(self, jugador: Client | str) -> int:
        """Obtiene la cantidad de canjes realizados por un jugador.

        Args:
            jugador: Jugador o nombre del jugador.

        Returns:
            Cantidad de canjes realizados.

        """
        return self._card_manager.cant_canjes(jugador)

    def canjear(self, jugador: Client | str, tarjetas: list[TarjetaDePais]) -> None:
        """Realiza un canje de tarjetas por unidades.

        Args:
            jugador: Jugador o nombre del jugador.
            tarjetas: Lista de tarjetas a canjear.

        """
        self._card_manager.canjear(jugador, tarjetas)

    def cant_jugadores(self) -> int:
        """Obtiene la cantidad de jugadores.

        Returns:
            Cantidad de jugadores.

        """
        return len(self.lista_jugadores())

    def mapa(self) -> Mapa:
        """Obtiene el mapa del juego.

        Returns:
            El mapa del juego.

        """
        return self._mapa

    def finalizar_turno(self) -> None:
        """Finaliza el turno actual y avanza al siguiente."""
        ronda_completada = self._turn_manager.avanzar_turno()
        num = self._turn_manager.id_turno_actual()
        cant_jugadores = self.cant_jugadores()

        if num == cant_jugadores or ronda_completada:
            # Verificar condición de victoria al final de la ronda
            ganador = self._victory_checker.verificar_condicion_victoria(
                self.lista_jugadores()
            )
            if ganador:
                # Alguien ganó la partida
                ganador_id = (
                    ganador.user_id() if hasattr(ganador, "user_id") else str(ganador)
                )
                ganador_nombre = (
                    ganador.username() if hasattr(ganador, "username") else str(ganador)
                )
                self._server.enviar_victoria(ganador_id, ganador_nombre)
                return  # No continuar con la siguiente ronda

            # Rotar la lista de jugadores para la nueva ronda
            jugadores = self.lista_jugadores()
            jugadores_rotados = self._turn_manager.rotar_jugadores(jugadores)

            jugadores_nombres = [
                j.username() if hasattr(j, "username") else str(j)
                for j in jugadores_rotados
            ]
            es_segundo_turno = isinstance(
                self._turn_manager.turno_actual(), PrimerTurno
            )
            self._turn_manager.iniciar_nueva_ronda(
                jugadores_nombres, es_segundo_turno=es_segundo_turno
            )

            # Notificar al servidor que se completó una ronda
            # para que actualice los colores de los jugadores
            self._server.enviar_colores_asignados()

    def jugadores(self) -> list[Client]:
        """Obtiene la lista de jugadores.

        Returns:
            Lista de jugadores.

        """
        return self._jugadores

    def lista_jugadores(self) -> list[Client]:
        """Obtiene la lista de jugadores.

        Returns:
            Lista de jugadores.

        """
        return self.jugadores()

    def lista_jugadores_orden_turno(self) -> list[str]:
        """Devuelve la lista de jugadores en el orden actual de los turnos.

        Returns:
            Lista de nombres de jugadores en el orden de los turnos.

        """
        return self._turn_manager.lista_jugadores_orden_turno(self.lista_jugadores())

    def atacar(
        self,
        pais_atacante: str,
        pais_defensor: str,
        cantidad_unidades: int | None = None,
    ) -> dict[str, Any]:
        """Realiza un ataque entre dos países.

        Returns:
            Diccionario con el resultado del ataque.

        Args:
            pais_atacante (str): País que inicia el ataque
            pais_defensor (str): País que recibe el ataque
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.

        """
        # Obtener las unidades de cada país
        unidades_atacante = self.mapa().cantidad_unidades(pais_atacante)
        unidades_defensor = self.mapa().cantidad_unidades(pais_defensor)

        # Calcular cuántos dados usar
        if cantidad_unidades is not None:
            # Validar que la cantidad esté en el rango válido (1-3)
            cantidad_unidades = max(1, min(3, cantidad_unidades))
            # Validar que no exceda las unidades disponibles (menos 1 que debe quedar)
            max_unidades_disponibles = unidades_atacante - 1
            cantidad_unidades = min(cantidad_unidades, max_unidades_disponibles)
            dados_atacante_count = cantidad_unidades
        else:
            dados_atacante_count = Batalla.calcular_cant_dados_atacante(
                unidades_atacante
            )

        dados_defensor_count = Batalla.calcular_cant_dados_defensor(unidades_defensor)

        # Generar dados aleatorios
        dados_atacante = sorted(
            [secrets.randbelow(6) + 1 for _ in range(dados_atacante_count)],
            reverse=True,
        )
        dados_defensor = sorted(
            [secrets.randbelow(6) + 1 for _ in range(dados_defensor_count)],
            reverse=True,
        )

        # Obtener nombres de los jugadores
        atacante_nombre = self.mapa().ocupado_por(pais_atacante)
        defensor_nombre = self.mapa().ocupado_por(pais_defensor)

        # Realizar la batalla
        print(f"Dados atacante ({atacante_nombre}): {dados_atacante}")
        print(f"Dados defensor ({defensor_nombre}): {dados_defensor}")

        resultado = Batalla.ataquen(
            atacante_nombre, defensor_nombre, dados_atacante, dados_defensor
        )

        print(f"Resultado batalla: {resultado}")
        print(f"Pérdidas: {resultado['restar']}")

        # Aplicar las pérdidas
        for perdedor in resultado["restar"]:
            if perdedor == atacante_nombre:
                print(f"Restando 1 unidad a {atacante_nombre} en {pais_atacante}")
                self.mapa().restar_una_unidad(pais_atacante)
            else:
                print(f"Restando 1 unidad a {defensor_nombre} en {pais_defensor}")
                self.mapa().restar_una_unidad(pais_defensor)

        # Verificar si el país defensor fue conquistado
        conquistado = False
        unidades_defensor_post_batalla = self.mapa().cantidad_unidades(pais_defensor)
        print(
            f"Unidades en {pais_defensor} después de batalla: "
            f"{unidades_defensor_post_batalla}"
        )

        if unidades_defensor_post_batalla == 0:
            # El atacante conquista el país
            print("=== CONQUISTA ===")
            atacante = self.mapa().ocupado_por(pais_atacante)
            print(f"Asignando {pais_defensor} a {atacante_nombre}")
            self.mapa().asignar_pais(atacante, pais_defensor)
            # Mover una unidad del atacante al país conquistado
            print(f"Moviendo 1 unidad de {pais_atacante} a {pais_defensor}")
            self.mapa().restar_una_unidad(pais_atacante)
            self.mapa().agregar_una_unidad(pais_defensor)
            conquistado = True

            print(f"{atacante_nombre} ha conquistado {pais_defensor}")
        else:
            print(f"El ataque de {atacante_nombre} a {pais_defensor} fue repelido")

        print(f"Ataque: {atacante_nombre} vs {defensor_nombre}")
        print(f"Dados atacante: {dados_atacante}, Dados defensor: {dados_defensor}")
        print(f"Resultado: {resultado}")

        # Retornar información completa de la batalla
        return {
            "origen": pais_atacante,
            "destino": pais_defensor,
            "atacante": atacante_nombre,
            "defensor": defensor_nombre,
            "dados_atacante": dados_atacante,
            "dados_defensor": dados_defensor,
            "resultado": resultado,
            "conquistado": conquistado,
        }

    def marcar_jugador_puede_reclamar(self, jugador: Client) -> None:
        """Marca a un jugador como elegible para reclamar tarjeta.

        Args:
            jugador: Jugador a marcar como elegible.

        """
        self._card_manager.marcar_jugador_puede_reclamar(jugador)

    def puede_reclamar_tarjeta(self, jugador: Client) -> bool:
        """Verifica si un jugador puede reclamar tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si el jugador puede reclamar tarjeta, False en caso contrario.

        """
        return self._card_manager.puede_reclamar_tarjeta(jugador)

    def reclamar_tarjeta_jugador(self, jugador: Client) -> None:
        """Remueve al jugador de la lista de elegibles tras reclamar.

        Args:
            jugador: Jugador que reclamó la tarjeta.

        """
        self._card_manager.reclamar_tarjeta_jugador(jugador)

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas (al finalizar turno)."""
        self._card_manager.limpiar_elegibilidad_reclamar()
