"""Mensajes de misiles (canjear, lanzar)."""

from __future__ import annotations

import json

from pyteg.client.msg.base import IMsg


class MsgCanjearMisil(IMsg):
    """Mensaje para canjear unidades por un misil."""

    def __init__(self, pais: str) -> None:
        """Crea un mensaje para canjear unidades por 1 misil en un país.

        Args:
            pais: Nombre del país donde se canjeará el misil.

        """
        self._tipo = "canjear_misil"
        self._pais = pais

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "pais": self._pais}
        return json.dumps(data)


class MsgLanzarMisil(IMsg):
    """Mensaje para lanzar un misil."""

    def __init__(self, pais_origen: str, pais_destino: str) -> None:
        """Crea un mensaje para lanzar un misil desde un país hacia otro.

        Args:
            pais_origen: País desde donde se lanza el misil.
            pais_destino: País objetivo del misil.

        """
        self._tipo = "lanzar_misil"
        self._pais_origen = pais_origen
        self._pais_destino = pais_destino

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "pais_origen": self._pais_origen,
            "pais_destino": self._pais_destino,
        }
        return json.dumps(data)
