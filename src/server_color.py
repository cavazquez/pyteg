import secrets
from copy import copy

from src.colores import Amarillo, Azul, Blanco, Cian, Magenta, Negro, Rojo, Verde


class ServerColor:
    def __init__(self):
        self._colores = [
            Rojo(),
            Verde(),
            Azul(),
            Amarillo(),
            Cian(),
            Magenta(),
            Negro(),
            Blanco(),
        ]
        self._usados = []

    def asignar_color_aleatorio(self, client):
        colores_disponibles = self.colores_disponibles()
        color = secrets.choice(colores_disponibles)
        self._usados.append(color)
        client.asignar_color(copy(color))

    def asignar_color(self, client, color_hexrgb):
        print(f"{color_hexrgb=}")
        color = [color_d.to_hex() for color_d in self.colores_disponibles()]
        print(f"{color=}")
        color = next(
            color_d
            for color_d in self.colores_disponibles()
            if color_hexrgb == color_d.to_hex()
        )
        if color not in self._usados:
            self._usados.append(color)
            client.asignar_color(copy(color))

    def colores(self):
        return self._colores

    def colores_disponibles(self):
        return [
            color for color in self._colores if color not in self._usados
        ]
