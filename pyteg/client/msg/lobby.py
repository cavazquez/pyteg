"""Mensajes de lobby/pre-partida (color, chat, username, empezar)."""

from __future__ import annotations

import json
from typing import Any

from pyteg.client.msg.base import LOG, IMsg


class MsgSeleccionarColor(IMsg):
    """Mensaje para seleccionar un color."""

    def __init__(self, color: Any) -> None:
        """Inicializa el mensaje de selección de color.

        Args:
            color: Color a seleccionar.

        """
        LOG.debug("MsgSeleccionarColor")
        self._tipo = "seleccionar_color"
        self._color = color

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "color": self._color.name()}
        LOG.debug("MsgSeleccionarColor to_json: %s", data)
        return json.dumps(data)


class MsgEmpezar(IMsg):
    """Mensaje para iniciar la partida."""

    def __init__(
        self,
        segundos: int | None = None,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Inicializa el mensaje para empezar la partida.

        Args:
            segundos: Segundos por turno.
            paises_para_victoria: Países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están habilitados.
            misiles_habilitados: Si los misiles están habilitados.

        """
        self._tipo = "empezar"
        self._segundos = segundos
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self._misiles_habilitados = misiles_habilitados

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data: dict[str, object] = {"mensaje": self._tipo}
        if self._segundos is not None:
            data["segundos"] = self._segundos
        if self._paises_para_victoria is not None:
            data["paises_para_victoria"] = self._paises_para_victoria
        data["objetivos_secretos"] = self._objetivos_secretos
        data["misiles_habilitados"] = self._misiles_habilitados
        return json.dumps(data)


class MsgChat(IMsg):
    """Mensaje de chat."""

    def __init__(self, msg: str) -> None:
        """Inicializa el mensaje de chat.

        Args:
            msg: Contenido del mensaje de chat.

        """
        self._tipo = "chat"
        self._msg = msg

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "msg": self._msg,
        }
        return json.dumps(data)


class MsgSetUsername(IMsg):
    """Mensaje para establecer el nombre de usuario."""

    def __init__(self, username: str) -> None:
        """Inicializa el mensaje para establecer el nombre de usuario.

        Args:
            username: Nombre de usuario a establecer.

        """
        self._tipo = "set_username"
        self._username = username

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "username": self._username}
        return json.dumps(data)


class MsgEmpezarPartida(IMsg):
    """Mensaje para iniciar la partida."""

    def __init__(self) -> None:
        """Inicializa el mensaje para iniciar la partida."""
        self._tipo = "empezar_partida"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data)
