"""Mensaje de fase autoritativa del turno."""

from __future__ import annotations

import json

from pyteg.server.msg.base import IMsg


class MsgFase(IMsg):
    """Notifica si el turno está colocando refuerzos o ejecutando acciones."""

    def __init__(self, fase: str, jugador_id: int, unidades_pendientes: int) -> None:
        """Inicializa la notificación de fase."""
        self._fase = fase
        self._jugador_id = jugador_id
        self._unidades_pendientes = unidades_pendientes

    def to_json(self) -> str:
        """Serializa la fase.

        Returns:
            JSON de la fase.

        """
        return json.dumps({
            "mensaje": "fase",
            "fase": self._fase,
            "jugador_id": self._jugador_id,
            "unidades_pendientes": self._unidades_pendientes,
        })
