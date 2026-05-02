"""Tareas del cliente del lobby (chat, admin, estado, colores, jugadores, mapa)."""

from __future__ import annotations

from pyteg.client.tasks.lobby.admin import ClientTaskSerAdmin
from pyteg.client.tasks.lobby.chat import ClientTaskChat, ClientTaskError
from pyteg.client.tasks.lobby.colores import (
    ClientTaskColor,
    ClientTaskColorAsignado,
)
from pyteg.client.tasks.lobby.estado import ClientTaskEstado
from pyteg.client.tasks.lobby.jugadores import (
    ClientTaskActualizarListaJugadores,
    ClientTaskUserId,
    ClientTaskUsername,
)
from pyteg.client.tasks.lobby.mapa import (
    ClientTaskAsignarPais,
    ClientTaskUnidadesDisponibles,
)

__all__ = [
    "ClientTaskActualizarListaJugadores",
    "ClientTaskAsignarPais",
    "ClientTaskChat",
    "ClientTaskColor",
    "ClientTaskColorAsignado",
    "ClientTaskError",
    "ClientTaskEstado",
    "ClientTaskSerAdmin",
    "ClientTaskUnidadesDisponibles",
    "ClientTaskUserId",
    "ClientTaskUsername",
]
