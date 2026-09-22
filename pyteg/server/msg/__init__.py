"""Mensajes tipados que el servidor envía a los clientes."""

from pyteg.server.msg.base import IMsg
from pyteg.server.msg.battle import MsgError, MsgResultadoBatalla, MsgVictoria
from pyteg.server.msg.cards_missiles import (
    MsgCanjeEspecial,
    MsgMisilAgregado,
    MsgReclamarTarjeta,
    MsgResultadoMisil,
    MsgSolicitarTarjetas,
    MsgTarjetasJugador,
)
from pyteg.server.msg.config import MsgConfiguracionPartida, MsgObjetivoSecreto
from pyteg.server.msg.connection import (
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEstado,
    MsgHello,
    MsgHelloAck,
    MsgPing,
    MsgReconexion,
    MsgSessionToken,
    MsgSosAdmin,
    MsgUserId,
    MsgUsername,
)
from pyteg.server.msg.fase import MsgFase
from pyteg.server.msg.map_turn import (
    MsgAgregarUnidad,
    MsgMoverUnidad,
    MsgPais,
    MsgTiempo,
    MsgTurno,
    MsgUnidadesDisponibles,
)
from pyteg.server.msg.players import MsgActualizarListaJugadores
from pyteg.server.msg.snapshot import MsgCommandResult, MsgSnapshot

__all__ = [
    "IMsg",
    "MsgActualizarListaJugadores",
    "MsgAgregarUnidad",
    "MsgCanjeEspecial",
    "MsgChat",
    "MsgColor",
    "MsgColorAsignado",
    "MsgCommandResult",
    "MsgConfiguracionPartida",
    "MsgError",
    "MsgEstado",
    "MsgFase",
    "MsgHello",
    "MsgHelloAck",
    "MsgMisilAgregado",
    "MsgMoverUnidad",
    "MsgObjetivoSecreto",
    "MsgPais",
    "MsgPing",
    "MsgReclamarTarjeta",
    "MsgReconexion",
    "MsgResultadoBatalla",
    "MsgResultadoMisil",
    "MsgSessionToken",
    "MsgSnapshot",
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
