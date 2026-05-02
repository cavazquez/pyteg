"""Mensajes de tiempo, turno, países y unidades en mapa."""

from __future__ import annotations

import json

from pyteg.server_msg.base import IMsg


class MsgTiempo(IMsg):
    """Mensaje para actualizar el tiempo restante del turno."""

    def __init__(self, userid_turno: int, tiempo_restante: int) -> None:
        """Inicializa el mensaje de tiempo.

        Args:
            userid_turno: ID del usuario en turno.
            tiempo_restante: Tiempo restante en segundos.

        """
        self._tipo = "tiempo"
        self._userid_turno = userid_turno
        self._tiempo_restante = tiempo_restante

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "user_id": self._userid_turno,
            "tiempo": self._tiempo_restante,
        }
        return json.dumps(data)


class MsgTurno(IMsg):
    """Mensaje para actualizar el turno actual del juego."""

    def __init__(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Inicializa el mensaje de turno.

        Args:
            num_turno: Número del turno actual.
            num_ronda: Número de la ronda actual.
            jugador_actual_id: ID del jugador en turno.
            jugador_actual_nombre: Nombre del jugador en turno.
            jugador_actual_color: Color del jugador en turno.

        """
        self._tipo = "turno"
        self._num_turno = num_turno
        self._num_ronda = num_ronda
        self._jugador_actual_id = jugador_actual_id
        self._jugador_actual_nombre = jugador_actual_nombre
        self._jugador_actual_color = jugador_actual_color

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "num_turno": self._num_turno,
            "num_ronda": self._num_ronda,
        }

        # Agregar información del jugador actual si está disponible
        if self._jugador_actual_id is not None:
            data["jugador_actual_id"] = self._jugador_actual_id
        if self._jugador_actual_nombre is not None:
            data["jugador_actual_nombre"] = self._jugador_actual_nombre
        if self._jugador_actual_color is not None:
            data["jugador_actual_color"] = self._jugador_actual_color

        return json.dumps(data)


class MsgPais(IMsg):
    """Mensaje para asignar un país a un jugador."""

    def __init__(self, pais: str, userid: int, unidades: int) -> None:
        """Inicializa el mensaje de país.

        Args:
            pais: Nombre del país.
            userid: ID del usuario propietario.
            unidades: Cantidad de unidades en el país.

        """
        self._tipo = "pais"
        self._pais = pais
        self._userid = userid
        self._unidades = unidades

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "userid": self._userid,
            "unidades": self._unidades,
        }
        return json.dumps(data)


class MsgAgregarUnidad(IMsg):
    """Mensaje para agregar unidades a un país."""

    def __init__(self, pais: str, tipo_unidad: str, cantidad: int) -> None:
        """Inicializa el mensaje de agregar unidad.

        Args:
            pais: Nombre del país.
            tipo_unidad: Tipo de unidad a agregar.
            cantidad: Cantidad de unidades a agregar.

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


class MsgUnidadesDisponibles(IMsg):
    """Mensaje para enviar las unidades disponibles del jugador."""

    def __init__(self, unidades: dict[str, int]) -> None:
        """Inicializa el mensaje de unidades disponibles.

        Args:
            unidades: Diccionario con el tipo de unidad y la cantidad disponible.

        """
        self._tipo = "unidades_disponibles"
        self._unidades = (
            unidades  # Diccionario con el tipo de unidad y la cantidad disponible
        )

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "unidades": self._unidades,
        }
        return json.dumps(data)


class MsgMoverUnidad(IMsg):
    """Mensaje para mover unidades entre países."""

    def __init__(self, origen: str, destino: str, cantidad: int) -> None:
        """Inicializa el mensaje de mover unidad.

        Args:
            origen: País de origen.
            destino: País de destino.
            cantidad: Cantidad de unidades a mover.

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
