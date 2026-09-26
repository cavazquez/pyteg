"""Rotación del orden de jugadores entre rondas."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class TurnOrderRotator:
    """Calcula el próximo orden sin guardar una copia del estado de los turnos."""

    def __init__(self, orden_actual: Callable[[], Sequence[int]]) -> None:
        """Recibe una consulta al orden vigente de los turnos."""
        self._orden_actual = orden_actual

    def rotar(self, jugadores_activos: Sequence[int]) -> list[int]:
        """Rota un puesto el orden vigente, quitando bajas y sumando altas.

        Args:
            jugadores_activos: Jugadores disponibles para la próxima ronda.

        Returns:
            Identificadores en el orden de la próxima ronda.

        """
        activos = list(dict.fromkeys(jugadores_activos))
        activos_set = set(activos)
        orden = list(
            dict.fromkeys(
                jugador_id
                for jugador_id in self._orden_actual()
                if jugador_id in activos_set
            )
        )
        presentes = set(orden)
        # Los reconectados sin turno vigente se agregan antes de rotar.
        orden.extend(
            jugador_id for jugador_id in activos if jugador_id not in presentes
        )
        if len(orden) > 1:
            return orden[1:] + orden[:1]
        return orden
