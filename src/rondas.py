import json

from src.turnos import SiguientesTurnos, SegundoTurno, PrimerTurno



class SiguientesRondas:
    def __proximo_turno(self, jugadores, mapa):
        for turno in [SiguientesTurnos(id_jugador, mapa) for id_jugador in jugadores]:
            yield turno

    def __init__(self, jugadores, game):
        print("Siguientes ronda")
        self._unidades = {}
        self._jugadores = jugadores
        self._turnos = self.__proximo_turno(jugadores, game.mapa())
        self._turno_actual = next(self._turnos)
        self._game = game

    def usar_unidad(self):
        self._turno_actual.usar_unidad()

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._turno_actual = next(self._turnos)
        except StopIteration:
            self._game._ronda = SiguientesRondas(self._jugadores, self._game)


class SegundaRonda:
    def __proximo_turno(self, jugadores):
        for turno in [SegundoTurno(id_jugador) for id_jugador in jugadores]:
            yield turno

    def __init__(self, jugadores, game):
        print("Segunda ronda")
        self._unidades = {}
        self._jugadores = jugadores
        self._turnos = self.__proximo_turno(jugadores)
        self._turno_actual = next(self._turnos)
        self._game = game

    def usar_unidad(self):
        self._turno_actual.usar_unidad()

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._turno_actual = next(self._turnos)
        except StopIteration:
            self._game._ronda = SiguientesRondas(self._jugadores, self._game)


class PrimeraRonda:
    def __proximo_turno(self, jugadores):
        for turno in [PrimerTurno(id_jugador) for id_jugador in jugadores]:
            yield turno

    def __init__(self, jugadores, game, server):
        print("Primera ronda")
        self._unidades = {}
        self._jugadores = jugadores
        self._turnos = self.__proximo_turno(jugadores)
        self._turno_actual = next(self._turnos)
        self._game = game

        print("Enviando jugadores")
        data = {"jugadores": jugadores}
        server.send_all(json.dumps(data))

    def usar_unidad(self):
        self._turno_actual.usar_unidad()
        print(self._unidades)

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._turno_actual = next(self._turnos)
        except StopIteration:
            self._game._ronda = SegundaRonda(self._jugadores, self._game)
