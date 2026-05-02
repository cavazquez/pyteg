"""Módulo para gestión de turnos del juego.

Este módulo encapsula la lógica de gestión de turnos y rondas,
separando esta responsabilidad del Game principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client
    from pyteg.server_mapa import Mapa

TurnoType = PrimerTurno | SegundoTurno | SiguientesTurnos


class TurnManager:
    """Gestiona los turnos y rondas del juego.

    Esta clase se encarga de toda la lógica relacionada con la gestión
    de turnos, incluyendo la creación de turnos, avance de turnos y rondas,
    y el orden de los jugadores.
    """

    def __init__(self, mapa: Mapa) -> None:
        """Inicializa el gestor de turnos.

        Args:
            mapa: Instancia del mapa del juego.

        """
        self._mapa = mapa
        self._turnos: list[TurnoType] = [PrimerTurno("NUllJugador")]
        self._num_turno = 0
        self._num_ronda = 1

    def inicializar_turnos(self, jugadores_nombres: list[str]) -> None:
        """Inicializa los turnos del juego con los jugadores.

        Args:
            jugadores_nombres: Lista de nombres de jugadores en orden.

        """
        self._turnos = [PrimerTurno(j) for j in jugadores_nombres]

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

    def avanzar_turno(self) -> bool:
        """Avanza al siguiente turno.

        Returns:
            True si se completó una ronda, False en caso contrario.

        """
        self._num_turno += 1
        return False

    def iniciar_nueva_ronda(
        self, jugadores_nombres: list[str], *, es_segundo_turno: bool = False
    ) -> None:
        """Inicia una nueva ronda con los jugadores rotados.

        Args:
            jugadores_nombres: Lista de nombres de jugadores en el nuevo orden.
            es_segundo_turno: Si True, crea SegundoTurno, sino SiguientesTurnos.

        """
        if es_segundo_turno:
            self._turnos = [SegundoTurno(j) for j in jugadores_nombres]
        else:
            self._turnos = [SiguientesTurnos(j, self._mapa) for j in jugadores_nombres]
        self._num_turno = 0
        self._num_ronda += 1

    def lista_jugadores_orden_turno(
        self, jugadores: list[Client] | None = None
    ) -> list[str]:
        """Devuelve la lista de jugadores en el orden actual de los turnos.

        Args:
            jugadores: Lista de jugadores del juego (opcional, para fallback).

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
        if not jugadores_orden and jugadores:
            return [j.username() for j in jugadores]

        return jugadores_orden

    def rotar_jugadores(self, jugadores: list[Client]) -> list[Client]:
        """Rota la lista de jugadores para la nueva ronda.

        Args:
            jugadores: Lista actual de jugadores.

        Returns:
            Lista de jugadores rotada.

        """
        if len(jugadores) > 1:
            return jugadores[1:] + jugadores[:1]  # Rotar a la izquierda
        return jugadores
