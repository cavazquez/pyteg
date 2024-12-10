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

    def asignar_color(self, client):
        colores_disponibles = [
            color for color in self._colores if color not in self._usados
        ]
        color = secrets.choice(colores_disponibles)
        self._usados.append(color)
        client.asignar_color(copy(color))

    def colores(self):
        return self._colores
