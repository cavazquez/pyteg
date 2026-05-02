"""Gestión de colores asignados a los jugadores."""

from __future__ import annotations

import contextlib
import secrets
from copy import copy
from typing import TYPE_CHECKING

from pyteg.colores import (
    Amarillo,
    Azul,
    Blanco,
    Cian,
    IColor,
    Magenta,
    Negro,
    Rojo,
    Verde,
)

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class ServerColor:
    """Gestiona la asignación de colores a los jugadores en el servidor."""

    def __init__(self) -> None:
        """Inicializa el gestor de colores con la lista de colores disponibles."""
        self._colores: list[IColor] = [
            Rojo(),
            Verde(),
            Azul(),
            Amarillo(),
            Cian(),
            Magenta(),
            Negro(),
            Blanco(),
        ]
        self._usados: list[IColor] = []

    def asignar_color_aleatorio(self, client: IClientProtocol) -> None:
        """Asigna un color aleatorio disponible a un cliente.

        Args:
            client: Cliente al que asignar el color.

        """
        colores_disponibles = self.colores_disponibles()
        color = secrets.choice(colores_disponibles)
        self.reservar_color(color)
        client.asignar_color(copy(color))

    def liberar_color(self, color: IColor | None) -> None:
        """Libera un color para que esté disponible nuevamente.

        Args:
            color: Color a liberar. Si es None, no hace nada.

        """
        if color is None:
            return
        with contextlib.suppress(ValueError):
            self.colores_usados().remove(color)

    def reservar_color(self, color: IColor) -> None:
        """Reserva un color para que no esté disponible.

        Args:
            color: Color a reservar.

        """
        self.colores_usados().append(color)

    def asignar_color(self, client: IClientProtocol, color_hexrgb: str) -> None:
        """Asigna un color específico a un cliente por su valor hexadecimal.

        Args:
            client: Cliente al que asignar el color.
            color_hexrgb: Valor hexadecimal del color (ej: "#FF0000").

        """
        color = self.obtener_color_de_hexrgb(color_hexrgb)
        if color and color not in self.colores_usados():
            color_actual = client.color_actual()
            self.liberar_color(color_actual)
            self.reservar_color(color)
            client.asignar_color(copy(color))

    def colores(self) -> list[IColor]:
        """Obtiene la lista de todos los colores disponibles.

        Returns:
            Lista de todos los colores.

        """
        return self._colores

    def colores_usados(self) -> list[IColor]:
        """Obtiene la lista de colores actualmente en uso.

        Returns:
            Lista de colores usados.

        """
        return self._usados

    def colores_disponibles(self) -> list[IColor]:
        """Obtiene la lista de colores disponibles (no usados).

        Returns:
            Lista de colores disponibles.

        """
        return [color for color in self.colores() if color not in self.colores_usados()]

    def obtener_color_de_hexrgb(self, hexrgb: str) -> IColor | None:
        """Obtiene un color por su valor hexadecimal.

        Args:
            hexrgb: Valor hexadecimal del color (ej: "#FF0000").

        Returns:
            El color correspondiente o None si no se encuentra.

        """
        for color in self.colores_disponibles():
            if hexrgb == color.to_hex():
                return color
        return None
