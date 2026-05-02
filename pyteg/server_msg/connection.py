"""Mensajes de conexión, chat y estado de sala."""

from __future__ import annotations

import json
from typing import Any

from pyteg.server_msg.base import IMsg


class MsgSosAdmin(IMsg):
    """Mensaje para notificar que el cliente es administrador."""

    def __init__(self) -> None:
        """Inicializa el mensaje de administrador."""
        self._tipo = "sosadmin"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgColorAsignado(IMsg):
    """Mensaje para notificar que se asignó un color a un jugador."""

    def __init__(self, id_user: int, rgb_json: str) -> None:
        """Inicializa el mensaje de color asignado.

        Args:
            id_user: ID del usuario al que se asignó el color.
            rgb_json: Representación JSON del color RGB.

        """
        self._tipo = "color_asignado"
        self._id_user = id_user
        self._rgb_json = rgb_json
        print(rgb_json)

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "id": self._id_user,
        }
        rgb_dict = json.loads(self._rgb_json)
        return json.dumps(data | rgb_dict)


class MsgColor(IMsg):
    """Mensaje para enviar un color disponible a los clientes."""

    def __init__(self, color: Any) -> None:
        """Inicializa el mensaje de color.

        Args:
            color: Objeto Color a enviar.

        """
        self._tipo = "color"
        self._color = color

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        color_json = json.loads(self._color.to_json())
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data | color_json)


class MsgChat(IMsg):
    """Mensaje de chat del servidor."""

    def __init__(self, msg: str, msg_type: str = "normal") -> None:
        """Inicializa el mensaje de chat.

        Args:
            msg: Contenido del mensaje.
            msg_type: Tipo de mensaje ("normal", "error", "system").

        """
        self._tipo = "chat"
        self._msg = msg
        self._msg_type = msg_type  # "normal", "error", "system"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "msg": self._msg,
            "msg_type": self._msg_type,
        }
        return json.dumps(data)


class MsgUserId(IMsg):
    """Mensaje para asignar un ID de usuario a un cliente."""

    def __init__(self, user_id: int) -> None:
        """Inicializa el mensaje de ID de usuario.

        Args:
            user_id: ID de usuario a asignar.

        """
        self._tipo = "user_id"
        self._user_id = user_id

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "user_id": self._user_id}
        return json.dumps(data)


class MsgUsername(IMsg):
    """Mensaje para actualizar el nombre de usuario de un jugador."""

    def __init__(self, userid: int, username: str) -> None:
        """Inicializa el mensaje de nombre de usuario.

        Args:
            userid: ID del usuario.
            username: Nombre de usuario.

        """
        self._tipo = "username"
        self._userid = userid
        self._username = username

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "username": self._username,
            "user_id": self._userid,
        }
        return json.dumps(data)


class MsgEstado(IMsg):
    """Mensaje para actualizar el estado del juego."""

    def __init__(self, estado: str) -> None:
        """Inicializa el mensaje de estado.

        Args:
            estado: Nuevo estado del juego.

        """
        self._tipo = "estado"
        self._estado = estado

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "estado": self._estado}
        return json.dumps(data)
