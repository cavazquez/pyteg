"""Mensajes del cliente al servidor (DTOs con `to_json()`).

Cada dominio de mensajes vive en su propio módulo; este paquete los
reexporta para preservar el contrato `from pyteg.client.msg import X`.
"""

from __future__ import annotations

from pyteg.client.msg.actions import (
    MsgAgregarUnidad,
    MsgAtacar,
    MsgFinalizarTurno,
    MsgMoverUnidad,
)
from pyteg.client.msg.base import IMsg
from pyteg.client.msg.cards import (
    MsgCanjearTarjetas,
    MsgCanjeEspecial,
    MsgReclamarTarjeta,
    MsgSolicitarTarjetas,
)
from pyteg.client.msg.lobby import (
    MsgChat,
    MsgEmpezar,
    MsgEmpezarPartida,
    MsgSeleccionarColor,
    MsgSetUsername,
)
from pyteg.client.msg.missiles import MsgCanjearMisil, MsgLanzarMisil

__all__ = [
    "IMsg",
    "MsgAgregarUnidad",
    "MsgAtacar",
    "MsgCanjeEspecial",
    "MsgCanjearMisil",
    "MsgCanjearTarjetas",
    "MsgChat",
    "MsgEmpezar",
    "MsgEmpezarPartida",
    "MsgFinalizarTurno",
    "MsgLanzarMisil",
    "MsgMoverUnidad",
    "MsgReclamarTarjeta",
    "MsgSeleccionarColor",
    "MsgSetUsername",
    "MsgSolicitarTarjetas",
]
