"""Tareas del cliente del flujo de juego (turno, tiempo, configuración, victoria)."""

from __future__ import annotations

from pyteg.client.tasks.game_flow.partida import (
    ClientTaskConfiguracionPartida,
    ClientTaskObjetivoSecreto,
    ClientTaskVictoria,
)
from pyteg.client.tasks.game_flow.turno import (
    ClientTaskTiempo,
    ClientTaskTurno,
)

__all__ = [
    "ClientTaskConfiguracionPartida",
    "ClientTaskObjetivoSecreto",
    "ClientTaskTiempo",
    "ClientTaskTurno",
    "ClientTaskVictoria",
]
