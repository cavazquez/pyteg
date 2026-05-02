"""Módulo para definir los mensajes que el cliente envía al servidor."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from pyteg.logger import get_logger

_LOG = get_logger("client.msg")


class IMsg(ABC):
    """Interfaz base para todos los mensajes del cliente."""

    @abstractmethod
    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje.

        """


class MsgSeleccionarColor(IMsg):
    """Mensaje para seleccionar un color."""

    def __init__(self, color: Any) -> None:
        """Inicializa el mensaje de selección de color.

        Args:
            color: Color a seleccionar.

        """
        _LOG.debug("MsgSeleccionarColor")
        self._tipo = "seleccionar_color"
        self._color = color

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo, "color": self._color.name()}
        _LOG.debug("MsgSeleccionarColor to_json: %s", data)
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


class MsgAgregarUnidad(IMsg):
    """Mensaje para agregar unidades a un país."""

    def __init__(self, pais: str, tipo_unidad: str, cantidad: int = 1) -> None:
        """Crea un mensaje para agregar unidades en un país específico.

        Args:
            pais: Nombre del país donde se agregará la unidad.
            tipo_unidad: Tipo de unidad a agregar (ej: 'infanteria', 'misil').
            cantidad: Cantidad de unidades a agregar. Defaults to 1.

        """
        self._tipo = "agregar_unidad"
        self._pais = pais
        self._tipo_unidad = tipo_unidad
        self._cantidad = cantidad

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "tipo_unidad": self._tipo_unidad,
            "cantidad": self._cantidad,
        }
        return json.dumps(data)


class MsgMoverUnidad(IMsg):
    """Mensaje para mover unidades entre países."""

    def __init__(self, origen: str, destino: str, cantidad: int = 1) -> None:
        """Crea un mensaje para mover unidades entre países.

        Args:
            origen: Nombre del país de origen.
            destino: Nombre del país de destino.
            cantidad: Cantidad de unidades a mover. Defaults to 1.

        """
        self._tipo = "mover_unidad"
        self._origen = origen
        self._destino = destino
        self._cantidad = cantidad

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
            "cantidad": self._cantidad,
        }
        return json.dumps(data)


class MsgAtacar(IMsg):
    """Mensaje para atacar un país desde otro."""

    def __init__(
        self, origen: str, destino: str, cantidad_unidades: int | None = None
    ) -> None:
        """Crea un mensaje para atacar de un país a otro.

        Args:
            origen: Nombre del país atacante.
            destino: Nombre del país defensor.
            cantidad_unidades: Cantidad de unidades con las que atacar (1-3).
                Si es None, se usa el máximo posible.

        """
        self._tipo = "atacar"
        self._origen = origen
        self._destino = destino
        self._cantidad_unidades = cantidad_unidades

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data: dict[str, object] = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
        }
        if self._cantidad_unidades is not None:
            data["cantidad_unidades"] = self._cantidad_unidades
        return json.dumps(data)


class MsgFinalizarTurno(IMsg):
    """Mensaje para finalizar el turno actual."""

    def __init__(self) -> None:
        """Crea un mensaje para finalizar el turno actual."""
        self._tipo = "finalizar_turno"

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {"mensaje": self._tipo}
        return json.dumps(data)


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
