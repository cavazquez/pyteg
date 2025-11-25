"""Gestión de colores asignados a los jugadores."""

from __future__ import annotations

import contextlib
import secrets
from copy import copy
from typing import Any

from src.colores import (
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


class ServerColor:
    def __init__(self) -> None:
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

    def asignar_color_aleatorio(self, client: Any) -> None:
        colores_disponibles = self.colores_disponibles()
        color = secrets.choice(colores_disponibles)
        self.reservar_color(color)
        client.asignar_color(copy(color))

    def liberar_color(self, color: IColor | None) -> None:
        if color is None:
            return
        with contextlib.suppress(ValueError):
            self.colores_usados().remove(color)

    def reservar_color(self, color: IColor) -> None:
        self.colores_usados().append(color)

    def asignar_color(self, client: Any, color_hexrgb: str) -> None:
        color = self.obtener_color_de_hexrgb(color_hexrgb)
        if color and color not in self.colores_usados():
            color_actual = client.color_actual()
            self.liberar_color(color_actual)
            self.reservar_color(color)
            client.asignar_color(copy(color))

    def colores(self) -> list[IColor]:
        return self._colores

    def colores_usados(self) -> list[IColor]:
        return self._usados

    def colores_disponibles(self) -> list[IColor]:
        return [color for color in self.colores() if color not in self.colores_usados()]

    def obtener_color_de_hexrgb(self, hexrgb: str) -> IColor | None:
        for color in self.colores_disponibles():
            if hexrgb == color.to_hex():
                return color
        return None
