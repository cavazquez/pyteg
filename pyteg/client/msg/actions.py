"""Mensajes de acciones de juego (agregar, mover, atacar, finalizar turno)."""

from __future__ import annotations

import json

from pyteg.client.msg.base import IMsg


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
