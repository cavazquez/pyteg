"""Módulo para gestión de turnos del juego.

Este módulo encapsula la lógica de gestión de turnos y rondas,
separando esta responsabilidad del Game principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pyteg.protocols import IClientProtocol
    from pyteg.server.juego.mapa import Mapa

TurnoType = PrimerTurno | SegundoTurno | SiguientesTurnos

# Userid placeholder usado antes de que se inicialicen los turnos reales.
_USERID_PLACEHOLDER = 0


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
        self._turnos: list[TurnoType] = [PrimerTurno(_USERID_PLACEHOLDER)]
        self._num_turno = 0
        self._num_ronda = 1

    def inicializar_turnos(self, jugadores_userids: list[int]) -> None:
        """Inicializa los turnos del juego con los jugadores.

        Args:
            jugadores_userids: Lista de userids (int) de jugadores en orden.

        """
        self._turnos = [PrimerTurno(j) for j in jugadores_userids]

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
        self, jugadores_userids: list[int], *, es_segundo_turno: bool = False
    ) -> None:
        """Inicia una nueva ronda con los jugadores rotados.

        Args:
            jugadores_userids: Lista de userids (int) de jugadores en el nuevo orden.
            es_segundo_turno: Si True, crea SegundoTurno, sino SiguientesTurnos.

        """
        if es_segundo_turno:
            self._turnos = [SegundoTurno(j) for j in jugadores_userids]
        else:
            self._turnos = [SiguientesTurnos(j, self._mapa) for j in jugadores_userids]
        self._num_turno = 0
        self._num_ronda += 1

    def lista_jugadores_orden_turno(
        self, jugadores: Sequence[IClientProtocol] | None = None
    ) -> list[int]:
        """Devuelve la lista de userids en el orden actual de los turnos.

        Args:
            jugadores: Lista de jugadores del juego (opcional, para fallback).

        Returns:
            Lista de userids (int) en el orden de los turnos.

        """
        jugadores_orden: list[int] = []
        for turno in self._turnos:
            jugador = turno.jugador_actual()
            if jugador not in jugadores_orden:
                jugadores_orden.append(jugador)

        if not jugadores_orden and jugadores:
            return [int(j.userid()) for j in jugadores]

        return jugadores_orden

    def rotar_jugadores(
        self, jugadores: Sequence[IClientProtocol]
    ) -> list[IClientProtocol]:
        """Rota la lista de jugadores para la nueva ronda.

        Args:
            jugadores: Lista actual de jugadores.

        Returns:
            Lista de jugadores rotada.

        """
        jugadores_list = list(jugadores)
        if len(jugadores_list) > 1:
            return jugadores_list[1:] + jugadores_list[:1]
        return jugadores_list
