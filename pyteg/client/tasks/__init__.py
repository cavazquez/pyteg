"""Tareas del cliente: mensaje del servidor → actualización de UI."""

from __future__ import annotations

from pyteg.client.tasks.base import ClientTaskNull, IClientTask
from pyteg.client.tasks.battle import ClientTaskResultadoBatalla
from pyteg.client.tasks.cards_missiles import (
    ClientTaskMisilAgregado,
    ClientTaskResultadoMisil,
    ClientTaskTarjetasJugador,
)
from pyteg.client.tasks.game_flow import (
    ClientTaskConfiguracionPartida,
    ClientTaskObjetivoSecreto,
    ClientTaskTiempo,
    ClientTaskTurno,
    ClientTaskVictoria,
)
from pyteg.client.tasks.lobby import (
    ClientTaskActualizarListaJugadores,
    ClientTaskAsignarPais,
    ClientTaskChat,
    ClientTaskColor,
    ClientTaskColorAsignado,
    ClientTaskError,
    ClientTaskEstado,
    ClientTaskSerAdmin,
    ClientTaskUnidadesDisponibles,
    ClientTaskUserId,
    ClientTaskUsername,
)

dict_task: dict[str, type[IClientTask]] = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
    "estado": ClientTaskEstado,
    "color_asignado": ClientTaskColorAsignado,
    "color": ClientTaskColor,
    "user_id": ClientTaskUserId,
    "username": ClientTaskUsername,
    "turno": ClientTaskTurno,
    "tiempo": ClientTaskTiempo,
    "pais": ClientTaskAsignarPais,
    "unidades_disponibles": ClientTaskUnidadesDisponibles,
    "actualizar_lista_jugadores": ClientTaskActualizarListaJugadores,
    "error": ClientTaskError,
    "resultado_batalla": ClientTaskResultadoBatalla,
    "victoria": ClientTaskVictoria,
    "configuracion_partida": ClientTaskConfiguracionPartida,
    "tarjetas_jugador": ClientTaskTarjetasJugador,
    "objetivo_secreto": ClientTaskObjetivoSecreto,
    "resultado_misil": ClientTaskResultadoMisil,
    "misil_agregado": ClientTaskMisilAgregado,
}

__all__ = [
    "ClientTaskActualizarListaJugadores",
    "ClientTaskAsignarPais",
    "ClientTaskChat",
    "ClientTaskColor",
    "ClientTaskColorAsignado",
    "ClientTaskConfiguracionPartida",
    "ClientTaskError",
    "ClientTaskEstado",
    "ClientTaskMisilAgregado",
    "ClientTaskNull",
    "ClientTaskObjetivoSecreto",
    "ClientTaskResultadoBatalla",
    "ClientTaskResultadoMisil",
    "ClientTaskSerAdmin",
    "ClientTaskTarjetasJugador",
    "ClientTaskTiempo",
    "ClientTaskTurno",
    "ClientTaskUnidadesDisponibles",
    "ClientTaskUserId",
    "ClientTaskUsername",
    "ClientTaskVictoria",
    "IClientTask",
    "dict_task",
]
