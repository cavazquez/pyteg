from collections import Counter
from itertools import cycle, starmap
from random import sample

from src.tarjeta_de_pais import TarjetaDePais


class Mazo:
    def __init__(self, paises, simbolos):
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta.pais] = tarjeta

    def build_tarjetas_de_paises(self, paises, simbolos):
        return list(starmap(TarjetaDePais, zip(paises, cycle(simbolos))))

    def cantidad_tarjetas(self):
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self):
        return sum([1 for tarjeta in self.tarjetas() if tarjeta.fue_usada() is True])

    def cantidad_tarjetas_asignadas(self):
        return sum([1 for tarjeta in self.tarjetas() if tarjeta.asignada() is True])

    def tarjetas(self):
        return list(self.mazo.values())

    def tarjetas_asignadas(self, jugador):
        return [tarjeta for tarjeta in self.tarjetas() if tarjeta.jugador() == jugador]

    def cant_tarjetas_asignadas(self, jugador):
        return sum([1 for tarjeta in self.tarjetas_asignadas(jugador)])

    def simbolo_asignado_almenos_3_tarjetas(self, jugador):
        return Counter(
            [tarjeta.simbolo for tarjeta in self.tarjetas_asignadas(jugador)],
        ).most_common(1)

    def dame_3_tarjetas_para_canje(self, jugador):
        simbolo = self.simbolo_asignado_almenos_3_tarjetas(jugador)[0]
        if simbolo[1] >= 3:
            return [
                tarjeta
                for tarjeta in self.tarjetas_asignadas(jugador)
                if tarjeta.simbolo == simbolo[0]
            ][:3]
        acum = set()
        res = []
        for tarjeta in self.tarjetas_asignadas(jugador):
            simbolo = tarjeta.simbolo
            if simbolo not in acum:
                res.append(tarjeta)
                acum.add(simbolo)
        return res[:3]

    def dame_simbolos(self):
        return {tarjeta.simbolo for tarjeta in self.tarjetas()}

    def liberar_tarjetas_usadas(self):
        for tarjeta in self.tarjetas():
            if tarjeta.fue_usada() and not tarjeta.asignada():
                tarjeta.desusar()

    def asignar_tarjeta(self, jugador, mezclar=sample):
        if self.cantidad_tarjetas_usadas() == self.cantidad_tarjetas():
            self.liberar_tarjetas_usadas()
        tarjetas = mezclar(self.tarjetas(), self.cantidad_tarjetas())
        for tarjeta in tarjetas:
            if tarjeta.se_puede_asignar():
                tarjeta.asignar(jugador)
                return tarjeta
        return None

    def desasignar_tarjetas(self, tarjetas):
        for tarjeta in tarjetas:
            tarjeta.desasignar()

    def __str__(self):
        res = ""
        for elem in self.mazo:
            res = res + elem + "\n"
        return res
