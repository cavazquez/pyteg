"""Tarjetas y misiles."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyteg.server.msg.base import IMsg

if TYPE_CHECKING:
    from pyteg.server.msg.types import MissileResultPayload


class MsgTarjetasJugador(IMsg):
    """Mensaje para enviar las tarjetas de un jugador."""

    def __init__(self, tarjetas: list[dict[str, str]]) -> None:
        """Inicializa un mensaje con las tarjetas del jugador.

        Args:
            tarjetas (list): Lista de tarjetas con formato
                [{"pais": str, "simbolo": str}, ...]

        """
        self._tipo = "tarjetas_jugador"
        self._tarjetas = tarjetas

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "tarjetas": self._tarjetas,
        }
        return json.dumps(data)


class MsgSolicitarTarjetas(IMsg):
    """Mensaje para solicitar las tarjetas del jugador al servidor."""

    def __init__(self) -> None:
        """Inicializa el mensaje de solicitar tarjetas."""
        self._tipo = "solicitar_tarjetas"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgReclamarTarjeta(IMsg):
    """Mensaje para reclamar una tarjeta después de conquistar un país."""

    def __init__(self) -> None:
        """Inicializa el mensaje de reclamar tarjeta."""
        self._tipo = "reclamar_tarjeta"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgCanjeEspecial(IMsg):
    """Mensaje para notificar un canje especial de país + tarjeta."""

    def __init__(self, pais: str, unidades_agregadas: int) -> None:
        """Inicializa el mensaje de canje especial.

        Args:
            pais: País donde se agregaron las unidades.
            unidades_agregadas: Cantidad de unidades agregadas.

        """
        self._tipo = "canje_especial"
        self._pais = pais
        self._unidades_agregadas = unidades_agregadas

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "unidades_agregadas": self._unidades_agregadas,
        }
        return json.dumps(data)


class MsgResultadoMisil(IMsg):
    """Mensaje para enviar el resultado del lanzamiento de un misil."""

    def __init__(self, resultado_data: MissileResultPayload) -> None:
        """Inicializa un mensaje con el resultado del lanzamiento de un misil.

        Args:
            resultado_data (dict): Diccionario con todos los datos del misil:
                - jugador_id (int): userid del jugador que lanzó el misil
                - jugador (str, opcional): Nombre del jugador (UI/chat)
                - pais_origen (str): País desde donde se lanzó
                - pais_destino (str): País atacado
                - distancia (int): Distancia entre países
                - dano (int): Daño causado (unidades perdidas)
                - unidades_restantes (int): Unidades que quedan en destino

        """
        self._tipo = "resultado_misil"
        self._jugador_id = resultado_data.get("jugador_id")
        self._jugador = resultado_data.get("jugador", "")
        self._pais_origen = resultado_data["pais_origen"]
        self._pais_destino = resultado_data["pais_destino"]
        self._distancia = resultado_data["distancia"]
        self._dano = resultado_data["dano"]
        self._unidades_restantes = resultado_data["unidades_restantes"]

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data: dict[str, Any] = {
            "mensaje": self._tipo,
            "jugador_id": self._jugador_id,
            "jugador": self._jugador,
            "pais_origen": self._pais_origen,
            "pais_destino": self._pais_destino,
            "distancia": self._distancia,
            "dano": self._dano,
            "unidades_restantes": self._unidades_restantes,
        }
        return json.dumps(data)


class MsgMisilAgregado(IMsg):
    """Mensaje para notificar que se agregó un misil a un país."""

    def __init__(self, pais: str, cantidad_misiles: int) -> None:
        """Inicializa un mensaje para notificar que se agregó un misil a un país.

        Args:
            pais (str): Nombre del país donde se agregó el misil
            cantidad_misiles (int): Cantidad total de misiles en el país

        """
        self._tipo = "misil_agregado"
        self._pais = pais
        self._cantidad_misiles = cantidad_misiles

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "cantidad_misiles": self._cantidad_misiles,
        }
        return json.dumps(data)
