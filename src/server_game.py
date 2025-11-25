"""Módulo para manejar la lógica del juego en el servidor."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from src.batalla import Batalla
from src.config import (
    DEFAULT_VICTORY_COUNTRIES,
    EXCHANGE_MULTIPLIER,
    EXCHANGE_UNITS,
    MAX_CARDS_BEFORE_FORCE_EXCHANGE,
)
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos

if TYPE_CHECKING:
    from src.mazo import Mazo
    from src.server import Server
    from src.server_client import Client
    from src.server_mapa import Mapa
    from src.tarjeta_de_pais import TarjetaDePais

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
        self._turnos: list[TurnoType] = [PrimerTurno("NUllJugador")]
        self._jugadores = jugadores
        self._num_turno = 0
        self._num_ronda = 1
        self._mazo = mazo
        self._cant_canjes: dict[str, int] = {}
        self._server = server  # Referencia al servidor para notificar cambios
        self._paises_para_victoria = paises_para_victoria
        self._jugadores_pueden_reclamar: set[Client] = (
            set()
        )  # Jugadores elegibles para reclamar tarjetas

    def empezar(self) -> None:
        """Inicia el juego asignando países y creando los primeros turnos."""
        jugadores = self.lista_jugadores()
        # Manejar tanto objetos Client como strings (para tests)
        jugadores_nombres = [
            j.username() if hasattr(j, "username") else str(j) for j in jugadores
        ]
        self._turnos = [PrimerTurno(j) for j in jugadores_nombres]
        self._mapa.asignar_paises(jugadores_nombres)
        self._cant_canjes = dict.fromkeys(jugadores_nombres, 0)
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
        return self._mazo

    def dame_una_tarjeta(self, jugador: Client) -> None:
        """Asigna una tarjeta a un jugador. Si tiene 5, fuerza un canje.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        cant_tarjetas_asignadas = self.mazo().cant_tarjetas_asignadas(jugador)
        if cant_tarjetas_asignadas == MAX_CARDS_BEFORE_FORCE_EXCHANGE:
            lista_3_tarjetas = self.mazo().dame_3_tarjetas_para_canje(jugador)
            self.canjear(jugador, lista_3_tarjetas)
        self.mazo().asignar_tarjeta(jugador)

    def turnos(self) -> list[TurnoType]:
        """Obtiene la lista de turnos.

        Returns:
            Lista de turnos.

        """
        return self._turnos

    def turno_actual(self) -> TurnoType:
        """Obtiene el turno actual.

        Returns:
            El turno actual.

        """
        if self._num_turno >= len(self._turnos):
            return self.turnos()[-1]
        return self.turnos()[self.id_turno_actual()]

    def id_turno_actual(self) -> int:
        """Obtiene el índice del turno actual.

        Returns:
            Índice del turno actual.

        """
        return self._num_turno

    def num_ronda(self) -> int:
        """Obtiene el número de ronda actual.

        Returns:
            Número de ronda.

        """
        return self._num_ronda

    def cant_canjes(self, jugador: Client | str) -> int:
        """Obtiene la cantidad de canjes realizados por un jugador.

        Args:
            jugador: Jugador o nombre del jugador.

        Returns:
            Cantidad de canjes realizados.

        """
        username = jugador.username() if hasattr(jugador, "username") else str(jugador)
        return self._cant_canjes.get(username, 0)

    def canjear(self, jugador: Client | str, tarjetas: list[TarjetaDePais]) -> None:
        """Realiza un canje de tarjetas por unidades.

        Args:
            jugador: Jugador o nombre del jugador.
            tarjetas: Lista de tarjetas a canjear.

        """
        cant_canjes = self.cant_canjes(jugador)
        turno = self._turnos[self._num_turno]
        cantidad_a_agregar = EXCHANGE_UNITS.get(
            cant_canjes, EXCHANGE_MULTIPLIER * cant_canjes
        )

        turno.agregar_unidades_generales(cantidad_a_agregar)
        self._mazo.desasignar_tarjetas(tarjetas)
        username = jugador.username() if hasattr(jugador, "username") else str(jugador)
        self._cant_canjes[username] = self._cant_canjes.get(username, 0) + 1

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
        self._num_turno += 1
        num = self._num_turno
        cant_jugadores = self.cant_jugadores()
        if num == cant_jugadores:
            # Verificar condición de victoria al final de la ronda
            ganador = self._verificar_condicion_victoria()
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
            if len(jugadores) > 1:
                jugadores = jugadores[1:] + jugadores[:1]  # Rotar a la izquierda

            jugadores_nombres = [
                j.username() if hasattr(j, "username") else str(j) for j in jugadores
            ]
            if isinstance(self.turno_actual(), PrimerTurno):
                self._turnos = [SegundoTurno(j) for j in jugadores_nombres]
            else:
                self._turnos = [
                    SiguientesTurnos(j, self.mapa()) for j in jugadores_nombres
                ]
            self._num_turno = 0
            self._num_ronda += 1

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
        # Obtener los jugadores en el orden de los turnos actuales
        jugadores_orden: list[str] = []
        for turno in self._turnos:
            jugador = turno.jugador_actual()
            if jugador not in jugadores_orden:
                jugadores_orden.append(jugador)

        # Si por alguna razón no hay jugadores
        # en los turnos, devolver la lista normal
        if not jugadores_orden:
            return [j.username() for j in self.lista_jugadores()]

        return jugadores_orden

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

    def _verificar_condicion_victoria(self) -> Client | None:
        """Verifica si algún jugador ha ganado la partida.

        Verifica si algún jugador ha ganado controlando el número objetivo
        de países o cumpliendo su objetivo secreto.

        Returns:
            El jugador ganador si existe, None en caso contrario.

        """
        total_paises = len(self._mapa.paises())

        # Si no hay países en el mapa, no puede haber ganador (edge case para tests)
        if total_paises == 0:
            return None

        # Verificar objetivos secretos si están activados
        if (
            hasattr(self._server, "_objetivos_secretos")
            and self._server._objetivos_secretos  # noqa: SLF001
        ):
            for jugador in self.lista_jugadores():
                if self._server.objetivos_secretos.verificar_condicion_victoria(
                    str(jugador.userid()),
                    self._mapa._mapa,  # noqa: SLF001
                    self._server.color,
                ):
                    jugador_nombre = (
                        jugador.username()
                        if hasattr(jugador, "username")
                        else str(jugador)
                    )
                    objetivo = self._server.objetivos_secretos.get_objetivo_jugador(
                        str(jugador.userid())
                    )
                    print(
                        f"¡{jugador_nombre} ha ganado cumpliendo su objetivo secreto!"
                    )
                    if objetivo:
                        print(f"Objetivo cumplido: {objetivo['descripcion']}")
                    return jugador

        # Verificar condición de victoria tradicional (por países)
        for jugador in self.lista_jugadores():
            jugador_nombre = (
                jugador.username() if hasattr(jugador, "username") else str(jugador)
            )
            paises_controlados = self._mapa.cantidad_de_paises_del_jugador(
                jugador_nombre
            )

            if self._paises_para_victoria == 0:
                objetivo_paises = total_paises
            else:
                objetivo_paises = self._paises_para_victoria

            if paises_controlados >= objetivo_paises:
                if self._paises_para_victoria == 0:
                    print(f"¡{jugador_nombre} ha ganado controlando todos los países!")
                else:
                    print(
                        f"¡{jugador_nombre} ha ganado controlando "
                        f"{paises_controlados} países!"
                    )
                return jugador

        return None

    def marcar_jugador_puede_reclamar(self, jugador: Client) -> None:
        """Marca a un jugador como elegible para reclamar tarjeta.

        Args:
            jugador: Jugador a marcar como elegible.

        """
        self._jugadores_pueden_reclamar.add(jugador)

    def puede_reclamar_tarjeta(self, jugador: Client) -> bool:
        """Verifica si un jugador puede reclamar tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si el jugador puede reclamar tarjeta, False en caso contrario.

        """
        return jugador in self._jugadores_pueden_reclamar

    def reclamar_tarjeta_jugador(self, jugador: Client) -> None:
        """Remueve al jugador de la lista de elegibles tras reclamar.

        Args:
            jugador: Jugador que reclamó la tarjeta.

        """
        self._jugadores_pueden_reclamar.discard(jugador)

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas (al finalizar turno)."""
        self._jugadores_pueden_reclamar.clear()
