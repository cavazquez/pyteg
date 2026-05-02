"""Tareas del servidor sobre acciones de juego (agregar/mover/atacar/turno).

Cada clase vive en su propio módulo (1 task = 1 archivo); este paquete
las reexporta para preservar el contrato `from pyteg.server.tasks.game_actions
import ServerTaskX`.
"""

from __future__ import annotations

from pyteg.server.tasks.game_actions.agregar_unidad import ServerTaskAgregarUnidad
from pyteg.server.tasks.game_actions.atacar import ServerTaskAtacar
from pyteg.server.tasks.game_actions.finalizar_turno import ServerTaskFinalizarTurno
from pyteg.server.tasks.game_actions.mover_unidad import ServerTaskMoverUnidad

__all__ = [
    "ServerTaskAgregarUnidad",
    "ServerTaskAtacar",
    "ServerTaskFinalizarTurno",
    "ServerTaskMoverUnidad",
]
