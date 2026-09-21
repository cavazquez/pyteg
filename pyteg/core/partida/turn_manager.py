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
        # Identidad lógica del turno actual. No depende de la posición en
        # ``_turnos``, que puede cambiar al quitar jugadores.
        self._turno_logico = 0

    def inicializar_turnos(self, jugadores_userids: list[int]) -> None:
        """Inicializa los turnos del juego con los jugadores.

        Args:
            jugadores_userids: Lista de userids (int) de jugadores en orden.

        """
        self._turnos = [PrimerTurno(j) for j in jugadores_userids]
        self._num_turno = 0
        self._turno_logico = 0

    def eliminar_jugador(self, jugador_id: int) -> bool:
        """Quita a un jugador de los turnos pendientes de la ronda.

        Si el jugador eliminado estaba antes del turno activo, ajusta el índice
        para que el turno activo siga apuntando al mismo jugador. El turno
        eliminado no puede reaparecer hasta que ``Game`` construya la siguiente
        ronda sólo con jugadores activos.

        Args:
            jugador_id: ``userid`` del jugador a retirar.

        Returns:
            ``True`` si se retiró un turno; ``False`` si ya no estaba presente.

        """
        indice = next(
            (
                indice
                for indice, turno in enumerate(self._turnos)
                if int(turno.jugador_actual()) == int(jugador_id)
            ),
            None,
        )
        if indice is None:
            return False

        era_turno_actual = indice == self._num_turno
        self._turnos.pop(indice)
        if indice < self._num_turno:
            self._num_turno -= 1
        elif era_turno_actual:
            # El jugador que sigue ocupa el turno activo sin pasar por
            # ``avanzar_turno`` (por ejemplo, después de una desconexión).
            self._turno_logico += 1
        if not self._turnos:
            self._num_turno = 0
        return True

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
            turno = self.turnos()[-1]
        else:
            turno = self.turnos()[self.id_turno_actual()]
        preparar = getattr(turno, "preparar", None)
        if callable(preparar):
            preparar()
        return turno

    def id_turno_actual(self) -> int:
        """Obtiene el índice del turno actual.

        Returns:
            Índice del turno actual.

        """
        return self._num_turno

    def clave_turno(self) -> tuple[int, int]:
        """Devuelve una identidad estable para el turno vigente.

        La posición de ``_num_turno`` es sólo un índice de presentación y
        puede retroceder cuando se quita un jugador anterior. ``_turno_logico``
        cambia únicamente al pasar al siguiente turno real.

        Returns:
            Tupla ``(ronda, identidad lógica del turno)``.

        """
        return self._num_ronda, self._turno_logico

    def ronda_completada(self) -> bool:
        """Indica si el índice actual ya no apunta a un turno pendiente.

        Returns:
            ``True`` cuando no quedan turnos después del índice actual.

        """
        return bool(self._turnos) and self._num_turno >= len(self._turnos)

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
        self._turno_logico += 1
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
        jugadores_por_id = {int(jugador.userid()): jugador for jugador in jugadores}
        orden_actual = [
            int(jugador_id)
            for jugador_id in self.lista_jugadores_orden_turno()
            if int(jugador_id) in jugadores_por_id
        ]
        # La lista histórica conserva identidades, pero no representa el orden
        # de la ronda vigente después de la primera rotación. Los jugadores que
        # aún no tengan turno (por ejemplo, una reconexión) quedan al final.
        ids_ordenados = orden_actual + [
            jugador_id
            for jugador_id in jugadores_por_id
            if jugador_id not in orden_actual
        ]
        jugadores_list = [jugadores_por_id[jugador_id] for jugador_id in ids_ordenados]
        if len(jugadores_list) > 1:
            return jugadores_list[1:] + jugadores_list[:1]
        return jugadores_list

    def reintegrar_jugador(self, jugador_id: int) -> bool:
        """Agrega un jugador reconectado al final de la ronda vigente.

        El jugador no se inserta delante del turno actual: así la reconexión no
        repite el turno en curso ni desplaza el índice que ya está siendo
        consumido. En la siguiente ronda participa con el orden resultante.

        Returns:
            ``True`` si se añadió el turno; ``False`` si ya estaba presente o
            todavía no había una ronda inicializada.

        """
        if any(
            int(turno.jugador_actual()) == int(jugador_id) for turno in self._turnos
        ):
            return False

        if not self._turnos:
            return False

        turno_actual = self._turnos[0]
        if isinstance(turno_actual, PrimerTurno):
            turno: TurnoType = PrimerTurno(jugador_id)
        elif isinstance(turno_actual, SegundoTurno):
            turno = SegundoTurno(jugador_id)
        else:
            turno = SiguientesTurnos(jugador_id, self._mapa)
        self._turnos.append(turno)
        return True
