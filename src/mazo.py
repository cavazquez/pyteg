from itertools import cycle
from random import sample

from src.tarjeta_de_pais import TarjetaDePais


class Mazo:
    def __init__(self, paises, simbolos):
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta] = [None, False]

    def build_tarjetas_de_paises(self, paises, simbolos):
        return [TarjetaDePais(*tupla) for tupla in zip(paises, cycle(simbolos))]

    def cantidad_tarjetas(self):
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self):
        return len([key for key in self.mazo.keys() if self.mazo[key][1] is True])

    def tarjetas(self):
        return [tarjeta for tarjeta in self.mazo.keys()]

    def jugador(self, tarjeta):
        return self.mazo[tarjeta][0]

    def tarjetas_asignadas(self, jugador):
        return sum(
            [1 for tarjeta in self.mazo.keys() if self.jugador(tarjeta) == jugador]
        )

    def liberar_tarjetas_usadas(self):
        for tarjeta in self.mazo.keys():
            if self.fue_usada(tarjeta) and not self.asignada(tarjeta):
                self.mazo[tarjeta][1] = False

    def asignar_tarjeta(self, jugador, mezclar=sample):
        if self.cantidad_tarjetas_usadas() == self.cantidad_tarjetas():
            self.liberar_tarjetas_usadas()
        tarjetas = mezclar(self.tarjetas(), self.cantidad_tarjetas())
        for tarjeta in tarjetas:
            if not (self.asignada(tarjeta) or self.fue_usada(tarjeta)):
                self.asignar(tarjeta, jugador)
                return tarjeta

    def liberar_tarjetas(self, tarjetas):
        for tarjeta in tarjetas:
            self.liberar(tarjeta)

    def asignada(self, tarjeta):
        return self.mazo[tarjeta][0] is not None

    def asignar(self, tarjeta, jugador):
        self.mazo[tarjeta][0] = jugador
        self.mazo[tarjeta][1] = True

    def fue_usada(self, tarjeta):
        return self.mazo[tarjeta][1]

    def liberar(self, tarjeta):
        self.mazo[tarjeta][0] = None

    def __str__(self):
        res = ""
        for elem in self.mazo:
            res = res + elem.__str__() + "\n"
        return res
