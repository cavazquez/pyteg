from itertools import cycle
from random import sample

from src.tarjeta_de_pais import TarjetaDePais


class Mazo:
    def __init__(self, paises, simbolos):
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta.dame_pais()] = tarjeta

    def build_tarjetas_de_paises(self, paises, simbolos):
        return [TarjetaDePais(*tupla) for tupla in zip(paises, cycle(simbolos))]

    def cantidad_tarjetas(self):
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self):
        return sum([1 for tarjeta in self.tarjetas() if tarjeta.fue_usada() is True])

    def cantidad_tarjetas_asignadas(self):
        return sum([1 for tarjeta in self.tarjetas() if tarjeta.asignada() is True])

    def tarjetas(self):
        return list(self.mazo.values())

    def jugador(self, tarjeta):
        return self.mazo[tarjeta][0]

    def tarjetas_asignadas(self, jugador):
        return len([1 for tarjeta in self.tarjetas() if tarjeta.jugador() == jugador])

    def liberar_tarjetas_usadas(self):
        for tarjeta in self.mazo.values():
            if tarjeta.fue_usada() and not tarjeta.asignada():
                tarjeta.desusar()

    def asignar_tarjeta(self, jugador, mezclar=sample):
        if self.cantidad_tarjetas_usadas() == self.cantidad_tarjetas():
            self.liberar_tarjetas_usadas()
        tarjetas = mezclar(self.tarjetas(), self.cantidad_tarjetas())
        for tarjeta in tarjetas:
            if tarjeta.se_puede_asignar():
                self.asignar(tarjeta, jugador)
                return tarjeta

    def liberar_tarjetas(self, tarjetas):
        for tarjeta in tarjetas:
            tarjeta.desasignar()

    def asignar(self, tarjeta, jugador):
        tarjeta.asignar(jugador)

    # def liberar(self, tarjeta):
    #    tarjeta.desasignar()

    def __str__(self):
        res = ""
        for elem in self.mazo:
            res = res + elem.__str__() + "\n"
        return res
