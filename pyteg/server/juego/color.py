"""Gestión de colores asignados a los jugadores."""

from __future__ import annotations

import contextlib
import secrets
import threading
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
        self._lock = threading.RLock()

    def asignar_color_aleatorio(self, client: IClientProtocol) -> bool:
        """Asigna un color aleatorio disponible a un cliente.

        Args:
            client: Cliente al que asignar el color.

        Returns:
            ``True`` si se reservó un color; ``False`` cuando la sala ya no
            tiene colores disponibles.

        """
        with self._lock:
            colores_disponibles = self._colores_disponibles()
            if not colores_disponibles:
                return False
            color = secrets.choice(colores_disponibles)
            self._usados.append(color)
            client.asignar_color(copy(color))
            return True

    def liberar_color(self, color: IColor | None) -> None:
        """Libera un color para que esté disponible nuevamente.

        Args:
            color: Color a liberar. Si es None, no hace nada.

        """
        if color is None:
            return
        with self._lock, contextlib.suppress(ValueError):
            self._usados.remove(color)

    def reservar_color(self, color: IColor) -> None:
        """Reserva un color para que no esté disponible.

        Args:
            color: Color a reservar.

        """
        with self._lock:
            if color not in self._usados:
                self._usados.append(color)

    def asignar_color(self, client: IClientProtocol, color_hexrgb: str) -> None:
        """Asigna un color específico a un cliente por su valor hexadecimal.

        Args:
            client: Cliente al que asignar el color.
            color_hexrgb: Valor hexadecimal del color (ej: "#FF0000").

        """
        with self._lock:
            color = self._obtener_color_de_hexrgb(color_hexrgb)
            if color is None:
                return
            color_actual = client.color_actual()
            if color_actual is not None:
                with contextlib.suppress(ValueError):
                    self._usados.remove(color_actual)
            self._usados.append(color)
            client.asignar_color(copy(color))

    def colores(self) -> list[IColor]:
        """Obtiene la lista de todos los colores disponibles.

        Returns:
            Lista de todos los colores.

        """
        with self._lock:
            return list(self._colores)

    def colores_usados(self) -> list[IColor]:
        """Obtiene la lista de colores actualmente en uso.

        Returns:
            Lista de colores usados.

        """
        with self._lock:
            return list(self._usados)

    def colores_disponibles(self) -> list[IColor]:
        """Obtiene la lista de colores disponibles (no usados).

        Returns:
            Lista de colores disponibles.

        """
        with self._lock:
            return self._colores_disponibles()

    def obtener_color_de_hexrgb(self, hexrgb: str) -> IColor | None:
        """Obtiene un color por su valor hexadecimal.

        Args:
            hexrgb: Valor hexadecimal del color (ej: "#FF0000").

        Returns:
            El color correspondiente o None si no se encuentra.

        """
        with self._lock:
            return self._obtener_color_de_hexrgb(hexrgb)

    def _colores_disponibles(self) -> list[IColor]:
        """Devuelve los colores libres mientras el lock ya está tomado.

        Returns:
            Colores sin reservar.

        """
        return [color for color in self._colores if color not in self._usados]

    def _obtener_color_de_hexrgb(self, hexrgb: str) -> IColor | None:
        """Busca un color libre mientras el lock ya está tomado.

        Returns:
            El color libre solicitado, o ``None`` si no está disponible.

        """
        for color in self._colores_disponibles():
            if hexrgb == color.to_hex():
                return color
        return None
