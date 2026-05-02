"""Mensajes tipados que el servidor envía a los clientes."""

from pyteg.server_msg.base import IMsg
from pyteg.server_msg.battle import MsgError, MsgResultadoBatalla, MsgVictoria
from pyteg.server_msg.cards_missiles import (
    MsgCanjeEspecial,
    MsgMisilAgregado,
    MsgReclamarTarjeta,
    MsgResultadoMisil,
    MsgSolicitarTarjetas,
    MsgTarjetasJugador,
)
from pyteg.server_msg.config import MsgConfiguracionPartida, MsgObjetivoSecreto
from pyteg.server_msg.connection import (
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEstado,
    MsgSosAdmin,
    MsgUserId,
    MsgUsername,
)
from pyteg.server_msg.map_turn import (
    MsgAgregarUnidad,
    MsgMoverUnidad,
    MsgPais,
    MsgTiempo,
    MsgTurno,
    MsgUnidadesDisponibles,
)
from pyteg.server_msg.players import MsgActualizarListaJugadores

__all__ = [
    "IMsg",
    "MsgActualizarListaJugadores",
    "MsgAgregarUnidad",
    "MsgCanjeEspecial",
    "MsgChat",
    "MsgColor",
    "MsgColorAsignado",
    "MsgConfiguracionPartida",
    "MsgError",
    "MsgEstado",
    "MsgMisilAgregado",
    "MsgMoverUnidad",
    "MsgObjetivoSecreto",
    "MsgPais",
    "MsgReclamarTarjeta",
    "MsgResultadoBatalla",
    "MsgResultadoMisil",
    "MsgSolicitarTarjetas",
    "MsgSosAdmin",
    "MsgTarjetasJugador",
    "MsgTiempo",
    "MsgTurno",
    "MsgUnidadesDisponibles",
    "MsgUserId",
    "MsgUsername",
    "MsgVictoria",
]
