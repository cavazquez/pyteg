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
        color = secrets.choice(self._colores)
        self._usados.append(color)
        self._colores.remove(color)
        client.asignar_color(copy(color))
