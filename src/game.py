from src.batalla import Batalla
from src.rondas import PrimeraRonda


class Game:
    def __init__(self, mapa):
        self._mapa = mapa
        self._start = False
        self._ronda = None
        self._jugadores = {}

    def agregar_una_unidad(self, pais):
        self._mapa.agregar_una_unidad(pais)
        self._ronda.usar_unidad()

    def start(self):
        self._ronda = PrimeraRonda(self._jugadores)
        self._mapa.asignar_paises(self._jugadores)
        self._start = True

    def ver_mapa(self):
        print("jugadores:", self._jugadores)
        if self._ronda:
            print("jugadores_ronda:", self._ronda._jugadores)
            print("turno_actual:", self._ronda._turno_actual.jugador_actual())
        print(self._mapa)

    def atacar(self, atacante, defensor):
        Batalla.ataquen(self._mapa, atacante, defensor)

    def reagrupar(self, desde, hacia, cantidad):
        self._mapa.mover(desde, hacia, cantidad)

    def ronda(self):
        return self._ronda

    def mapa(self):
        return self._mapa

    def jugadores(self):
        return self._jugadores

    def agregar_jugador(self, id_j, nombre):
        if id_j not in self._jugadores:
            self._jugadores[id_j] = nombre
