from src.batalla import Batalla
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class Game:
    def __init__(self, mapa):
        self._mapa = mapa
        self._start = False
        self._turnos = None
        self._jugadores = {}
        self._num_turno = 0

    def agregar_una_unidad(self, pais):
        self._mapa.agregar_una_unidad(pais)
        self._ronda.usar_unidad()

    def empezar(self):
        self._turnos = [PrimerTurno(j) for j in self.lista_jugadores()]
        self._mapa.asignar_paises(self.lista_jugadores())
        self._start = True

    def empezo(self):
        return self._start

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

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self._num_turno

    def cant_jugadores(self):
        return len(self.lista_jugadores())

    def mapa(self):
        return self._mapa

    def finalizar_turno(self):
        self._num_turno += 1
        num = self._num_turno 
        cant_jugadores = self.cant_jugadores()
        if num == cant_jugadores:
            self._turnos = [SegundoTurno(j) for j in self.lista_jugadores()]
            return 

        if num % (cant_jugadores) == 0:
            self._turnos = [
                    SiguientesTurnos(j, self.mapa()) for j in self.lista_jugadores()]



    def jugadores(self):
        return self._jugadores

    def lista_jugadores(self):
        return list(self.jugadores().values())

    def agregar_jugador(self, id_j, nombre):
        if id_j not in self._jugadores:
            self._jugadores[id_j] = nombre
