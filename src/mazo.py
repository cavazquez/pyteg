from src.tarjeta_de_pais import TarjetaDePais
from itertools import cycle
from random import sample


class Mazo:
    def __init__(self, paises, simbolos):
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo = []
        for tarjeta in tarjetas:
            self.mazo.append([tarjeta, None])

    def build_tarjetas_de_paises(self, paises, simbolos):
        return [TarjetaDePais(*tupla) for tupla in zip(paises, cycle(simbolos))]

    def cantidad_tarjetas(self):
        return len(self.mazo)

    def tarjetas(self):
        return [tarjeta for tarjeta, _ in self.mazo]

    def tarjetas_asignadas(self, jugador):
        return sum([1 for tarjeta in self.mazo if tarjeta[1] == jugador])

    def asignar_tarjeta(self, jugador):
        self.mazo = sample(self.mazo, self.cantidad_tarjetas())
        for i, tarjeta in enumerate(self.mazo):
            if not self.mazo[i][1]:
                self.mazo[i][1] = jugador
                return self.mazo[i][0]

    def liberar_tarjetas(self, tarjetas):
        for tarjeta in tarjetas:
            for elem in self.mazo:
                if tarjeta == elem[0]:
                    elem[1] = None
