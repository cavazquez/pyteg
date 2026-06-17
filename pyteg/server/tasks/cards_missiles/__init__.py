"""Tareas del servidor relacionadas con tarjetas y misiles.

Cada clase vive en su propio módulo (1 task = 1 archivo); este paquete
las reexporta para preservar el contrato `from pyteg.server.tasks.cards_missiles
import ServerTaskX`.
"""

from __future__ import annotations

from pyteg.server.tasks.cards_missiles.canje_especial import ServerTaskCanjeEspecial
from pyteg.server.tasks.cards_missiles.canjear_misil import ServerTaskCanjearMisil
from pyteg.server.tasks.cards_missiles.canjear_tarjetas import ServerTaskCanjearTarjetas
from pyteg.server.tasks.cards_missiles.lanzar_misil import ServerTaskLanzarMisil
from pyteg.server.tasks.cards_missiles.reclamar_tarjeta import ServerTaskReclamarTarjeta
from pyteg.server.tasks.cards_missiles.solicitar_tarjetas import (
    ServerTaskSolicitarTarjetas,
)

__all__ = [
    "ServerTaskCanjeEspecial",
    "ServerTaskCanjearMisil",
    "ServerTaskCanjearTarjetas",
    "ServerTaskLanzarMisil",
    "ServerTaskReclamarTarjeta",
    "ServerTaskSolicitarTarjetas",
]
