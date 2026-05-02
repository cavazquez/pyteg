"""Tareas del servidor: mensaje del cliente → acción validada."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pyteg.server_tasks.base import LOGGER, IServerTask, ServerTaskNull
from pyteg.server_tasks.cards_missiles import (
    ServerTaskCanjearMisil,
    ServerTaskCanjeEspecial,
    ServerTaskLanzarMisil,
    ServerTaskReclamarTarjeta,
    ServerTaskSolicitarTarjetas,
)
from pyteg.server_tasks.game_actions import (
    ServerTaskAgregarUnidad,
    ServerTaskAtacar,
    ServerTaskFinalizarTurno,
    ServerTaskMoverUnidad,
)
from pyteg.server_tasks.lobby import (
    ServerTaskChat,
    ServerTaskEmpezar,
    ServerTaskEmpezarPartida,
    ServerTaskSeleccionarColor,
    ServerTaskSetUsername,
)

TaskFactory = Callable[[dict[str, Any]], IServerTask]

dict_task: dict[str, TaskFactory] = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "empezar_partida": ServerTaskEmpezarPartida,
    "set_username": ServerTaskSetUsername,
    "agregar_unidad": ServerTaskAgregarUnidad,
    "mover_unidad": ServerTaskMoverUnidad,
    "atacar": ServerTaskAtacar,
    "finalizar_turno": ServerTaskFinalizarTurno,
    "solicitar_tarjetas": ServerTaskSolicitarTarjetas,
    "reclamar_tarjeta": ServerTaskReclamarTarjeta,
    "canje_especial": ServerTaskCanjeEspecial,
    "canjear_misil": ServerTaskCanjearMisil,
    "lanzar_misil": ServerTaskLanzarMisil,
}

__all__ = [
    "LOGGER",
    "IServerTask",
    "ServerTaskAgregarUnidad",
    "ServerTaskAtacar",
    "ServerTaskCanjeEspecial",
    "ServerTaskCanjearMisil",
    "ServerTaskChat",
    "ServerTaskEmpezar",
    "ServerTaskEmpezarPartida",
    "ServerTaskFinalizarTurno",
    "ServerTaskLanzarMisil",
    "ServerTaskMoverUnidad",
    "ServerTaskNull",
    "ServerTaskReclamarTarjeta",
    "ServerTaskSeleccionarColor",
    "ServerTaskSetUsername",
    "ServerTaskSolicitarTarjetas",
    "TaskFactory",
    "dict_task",
]
