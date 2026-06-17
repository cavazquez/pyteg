"""Mensajes de tarjetas (solicitar, reclamar, canje especial y canje triple)."""

from __future__ import annotations

import json
from typing import Any

from pyteg.client.msg.base import IMsg


class MsgSolicitarTarjetas(IMsg):
    """Mensaje para solicitar las tarjetas del jugador."""

    def __init__(self) -> None:
        """Crea un mensaje para solicitar las tarjetas del jugador."""
        self._tipo = "solicitar_tarjetas"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgReclamarTarjeta(IMsg):
    """Mensaje para reclamar una tarjeta."""

    def __init__(self) -> None:
        """Crea un mensaje para reclamar una tarjeta."""
        self._tipo = "reclamar_tarjeta"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgCanjeEspecial(IMsg):
    """Mensaje para canje especial de país + tarjeta."""

    def __init__(self, pais: str) -> None:
        """Crea un mensaje para canje especial de país + tarjeta.

        Args:
            pais: Nombre del país para el canje especial.

        """
        self._tipo = "canje_especial"
        self._pais = pais

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "pais": self._pais}
        return json.dumps(data)


class MsgCanjearTarjetas(IMsg):
    """Mensaje para canjear tres tarjetas del jugador."""

    def __init__(self, tarjetas: list[dict[str, Any]]) -> None:
        """Crea un mensaje de canje de tres tarjetas.

        Args:
            tarjetas: Lista con datos de cada tarjeta (pais, simbolo).

        """
        self._tipo = "canjear_tarjetas"
        self._tarjetas = tarjetas

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "tarjetas": self._tarjetas}
        return json.dumps(data)
