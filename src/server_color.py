import contextlib
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
        self.reservar_color(color)
        client.asignar_color(copy(color))

    def liberar_color(self, color):
        with contextlib.suppress(ValueError):
            self.colores_usados().remove(color)

    def reservar_color(self, color):
        self.colores_usados().append(color)

    def asignar_color(self, client, color_hexrgb):
        color = self.obtener_color_de_hexrgb(color_hexrgb)
        if color and color not in self.colores_usados():
            color_actual = client.color_actual()
            self.liberar_color(color_actual)
            self.reservar_color(color)
            client.asignar_color(copy(color))

    def colores(self):
        return self._colores

    def colores_usados(self):
        return self._usados

    def colores_disponibles(self):
        return [color for color in self.colores() if color not in self.colores_usados()]

    def obtener_color_de_hexrgb(self, hexrgb):
        for color in self.colores_disponibles():
            if hexrgb == color.to_hex():
                return color
        return None
