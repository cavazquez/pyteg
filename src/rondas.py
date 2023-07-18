from src.turnos import SiguientesTurnos, SegundoTurno, PrimerTurno


class SiguientesRondas:
    def __init__(self, jugadores, mapa):
        self._unidades = {}
        self._jugadores = jugadores
        self._turnos = [SiguientesTurnos(id_jugador, mapa) for id_jugador in jugadores]
        self._turno_actual = self.turnos()[0]
        self._num_turno_actual = 0

    def usar_unidad(self):
        self._turno_actual.usar_unidad()

    def jugadores(self):
        return self._jugadores

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._num_turno_actual += 1
            self._turno_actual = self.turnos()[self._num_turno_actual]
        except IndexError:
            self._turno_actual = None


class SegundaRonda:
    def __init__(self, jugadores):
        self._unidades = {}
        self._jugadores = jugadores
        self._turnos = [SegundoTurno(id_jugador) for id_jugador in jugadores]
        self._turno_actual = self._turnos[0]
        self._num_turno_actual = 0

    def usar_unidad(self):
        self._turno_actual.usar_unidad()

    def jugadores(self):
        return self._jugadores

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._num_turno_actual += 1
            self._turno_actual = self.turnos()[self._num_turno_actual]
        except IndexError:
            self._turno_actual = None


class PrimeraRonda:
    def __init__(self, jugadores):
        self._jugadores = jugadores
        self._turnos = [PrimerTurno(id_jugador) for id_jugador in jugadores]
        self._turno_actual = self._turnos[0]
        self._num_turno_actual = 0

    def jugadores(self):
        return self._jugadores

    def turnos(self):
        return self._turnos

    def usar_unidad(self):
        self._turno_actual.usar_unidad()

    def turno_actual(self):
        return self._turno_actual

    def finalizar_turno(self):
        try:
            self._num_turno_actual += 1
            self._turno_actual = self.turnos()[self._num_turno_actual]
        except IndexError:
            self._turno_actual = None
