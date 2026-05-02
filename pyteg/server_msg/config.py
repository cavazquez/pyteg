"""Configuración de partida y objetivos secretos."""

from __future__ import annotations

import json

from pyteg.server_msg.base import IMsg


class MsgConfiguracionPartida(IMsg):
    """Mensaje para enviar la configuración de la partida."""

    def __init__(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Inicializa un mensaje con la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
            objetivos_secretos (bool): Si los objetivos secretos están activados
            misiles_habilitados (bool): Si el sistema de misiles está habilitado

        """
        self._tipo = "configuracion_partida"
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self._misiles_habilitados = misiles_habilitados

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "segundos_por_turno": self._segundos_por_turno,
            "paises_para_victoria": self._paises_para_victoria,
            "objetivos_secretos": self._objetivos_secretos,
            "misiles_habilitados": self._misiles_habilitados,
        }
        return json.dumps(data)


class MsgObjetivoSecreto(IMsg):
    """Mensaje para enviar el objetivo secreto asignado a un jugador."""

    def __init__(self, objetivo_id: str, descripcion: str) -> None:
        """Inicializa un mensaje con el objetivo secreto asignado al jugador.

        Args:
            objetivo_id (str): ID del objetivo secreto
            descripcion (str): Descripción del objetivo secreto

        """
        self._tipo = "objetivo_secreto"
        self._objetivo_id = objetivo_id
        self._descripcion = descripcion

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "objetivo_id": self._objetivo_id,
            "descripcion": self._descripcion,
        }
        return json.dumps(data)
