"""Batalla, errores y victoria."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyteg.server.msg.base import IMsg

if TYPE_CHECKING:
    from pyteg.server.msg.types import BattleResultPayload


class MsgResultadoBatalla(IMsg):
    """Mensaje para enviar el resultado de una batalla."""

    def __init__(self, batalla_data: BattleResultPayload) -> None:
        """Inicializa un mensaje con el resultado de una batalla.

        Args:
            batalla_data (dict): Diccionario con todos los datos de la batalla:
                - origen (str): País atacante
                - destino (str): País defensor
                - atacante_id (int|None): userid del jugador atacante
                - defensor_id (int|None): userid del jugador defensor
                - atacante (str): Nombre del jugador atacante (UI/chat)
                - defensor (str): Nombre del jugador defensor (UI/chat)
                - dados_atacante (list): Lista de dados del atacante
                - dados_defensor (list): Lista de dados del defensor
                - resultado (dict): Resultado de la batalla con pérdidas
                - conquistado (bool): Si el país fue conquistado

        """
        self._tipo = "resultado_batalla"
        self._origen = batalla_data["origen"]
        self._destino = batalla_data["destino"]
        self._atacante_id = batalla_data.get("atacante_id")
        self._defensor_id = batalla_data.get("defensor_id")
        self._atacante = batalla_data.get("atacante", "")
        self._defensor = batalla_data.get("defensor", "")
        self._dados_atacante = batalla_data["dados_atacante"]
        self._dados_defensor = batalla_data["dados_defensor"]
        self._resultado = batalla_data["resultado"]
        self._conquistado = batalla_data.get("conquistado", False)

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data: dict[str, Any] = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
            "atacante_id": self._atacante_id,
            "defensor_id": self._defensor_id,
            "atacante": self._atacante,
            "defensor": self._defensor,
            "dados_atacante": self._dados_atacante,
            "dados_defensor": self._dados_defensor,
            "resultado": self._resultado,
            "conquistado": self._conquistado,
        }
        return json.dumps(data)


class MsgError(IMsg):
    """Mensaje para enviar errores del servidor a los clientes."""

    def __init__(self, error_type: str, message: str) -> None:
        """Inicializa un mensaje de error del servidor.

        Args:
            error_type (str): Tipo de error (ej: "duplicate_username")
            message (str): Mensaje descriptivo del error

        """
        self._tipo = "error"
        self._error_type = error_type
        self._message = message

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "error_type": self._error_type,
            "message": self._message,
        }
        return json.dumps(data)


class MsgVictoria(IMsg):
    """Mensaje para notificar la victoria de un jugador."""

    def __init__(self, ganador_id: int, ganador_nombre: str) -> None:
        """Inicializa un mensaje de victoria.

        Args:
            ganador_id: userid (int) del jugador ganador.
            ganador_nombre: Nombre del jugador ganador (UI/chat).

        """
        self._tipo = "victoria"
        self._ganador_id = ganador_id
        self._ganador_nombre = ganador_nombre

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data: dict[str, Any] = {
            "mensaje": self._tipo,
            "ganador_id": self._ganador_id,
            "ganador_nombre": self._ganador_nombre,
        }
        return json.dumps(data)
