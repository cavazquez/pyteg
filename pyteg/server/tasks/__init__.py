"""Tareas del servidor: mensaje del cliente → acción validada."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pyteg.server.tasks.base import LOGGER, IServerTask, ServerTaskNull
from pyteg.server.tasks.cards_missiles import (
    ServerTaskCanjearMisil,
    ServerTaskCanjeEspecial,
    ServerTaskLanzarMisil,
    ServerTaskReclamarTarjeta,
    ServerTaskSolicitarTarjetas,
)
from pyteg.server.tasks.game_actions import (
    ServerTaskAgregarUnidad,
    ServerTaskAtacar,
    ServerTaskFinalizarTurno,
    ServerTaskMoverUnidad,
)
from pyteg.server.tasks.lobby import (
    ServerTaskChat,
    ServerTaskEmpezar,
    ServerTaskEmpezarPartida,
    ServerTaskSeleccionarColor,
    ServerTaskSetUsername,
)
from pyteg.server.tasks.types import BaseTaskData

# Cada factory acepta `BaseTaskData` (el TypedDict mínimo) y devuelve una
# tarea concreta. Las subclases tipan internamente su propio TypedDict via
# `IServerTask[XTaskData]` y un cast en su `__init__`.
TaskFactory = Callable[[Any], IServerTask[Any]]

dict_task: dict[str, TaskFactory] = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "empezar_partida": ServerTaskEmpezarPartida,
    "seleccionar_color": ServerTaskSeleccionarColor,
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
    "BaseTaskData",
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
