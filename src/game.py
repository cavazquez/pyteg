from src.batalla import Batalla
from src.mapa import Mapa
from src.rondas import PrimeraRonda
from src.utils import build_mapa


class Game:
    def __init__(self, server):
        self._mapa = Mapa(build_mapa)
        self._start = False
        self._ronda = None
        self._jugadores = []
        self._server = server

    def agregar_una_unidad(self, pais):
        self._mapa.agregar_una_unidad(pais)
        self._ronda.usar_unidad()

    def start(self, server):
        self._jugadores = self._server.dame_lista_jugadores()
        self._ronda = PrimeraRonda(self._jugadores, self, server)
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
