import json
from random import sample, shuffle

from utils import build_mapa


class Mapa:

    def __init__(self):
        self._mapa = build_mapa()

    def agregar_una_unidad(self, pais):
        self._mapa[pais][0] += 1

    def cantidad_unidades(self, pais):
        return self._mapa[pais][0]

    def set_unidades(self, pais, cant):
        self._mapa[pais][0] = cant

    def mover(self, desde, hacia, cantidad):
        self._mapa[desde][0] -= cantidad
        self._mapa[hacia][0] += cantidad

    def continente(self, pais):
        return self._mapa[pais][1]

    def ocupado_por(self, pais):
        return self._mapa[pais][2]

    def paises(self):
        return [pais for pais in self._mapa]

    def asignar_paises(self, jugadores):
        paises = self.paises()
        cant = len(paises) // len(jugadores)
        for jug in jugadores:
            paises_elegidos = sample(paises, k=cant)
            for pais in paises_elegidos:
                self.asignar_pais(jug, pais)
            paises = [pais for pais in paises if pais not in paises_elegidos]

        shuffle(jugadores)
        for jug, pais in zip(jugadores, paises):
            self.asignar_pais(jug, pais)

    def cantidad_de_paises_por_continente(self, continente):
        return len([pais for pais in self.paises() if self.continente(pais) == continente])

    def asignar_pais(self, jugador, pais):
        self._mapa[pais][2] = jugador

    def cantidad_de_paises_del_jugador(self, jugador):
        return len([ pais for pais in self.paises() if self.ocupado_por(pais) == jugador])

    def cantidad_de_paises_del_jugador_por_continente(self, jugador, continente):
        return len([ pais for pais in self.paises() if self.ocupado_por(pais) == jugador and self.continente(pais) == continente])

    def tiene_toda_europa(self, jugador):
        continente = 'Europa'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_asia(self, jugador):
        continente = 'Asia'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_oceania(self, jugador):
        continente = 'Oceania'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_africa(self, jugador):
        continente = 'Africa'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_america_del_sur(self, jugador):
        continente = 'Sudamerica'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_america_del_norte(self, jugador):
        continente = 'Norteamerica'
        return self.cantidad_de_paises_del_jugador_por_continente(jugador, continente) == self.cantidad_de_paises_por_continente(continente)

    def __str__(self):
        return json.dumps(self._mapa)
