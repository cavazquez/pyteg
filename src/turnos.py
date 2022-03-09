from src.calculos import Calculos


class SiguientesTurnos:

    def __init__(self, jugador, mapa):
        self._jugador = jugador
        self._unidades = Calculos.calcular_unidades_generales(mapa, jugador)
        self._unidades_europa = Calculos.calcular_unidades_europa(mapa, jugador)
        self._unidades_africa = Calculos.calcular_unidades_africa(mapa, jugador)
        self._unidades_america_del_sur = Calculos.calcular_unidades_america_del_sur(mapa, jugador)
        self._unidades_america_del_norte = Calculos.calcular_unidades_america_del_norte(mapa, jugador)
        self._unidades_asia = Calculos.calcular_unidades_asia(mapa, jugador)
        self._unidades_oceania = Calculos.calcular_unidades_oceania(mapa, jugador)

    def jugador_actual(self):
        return self._jugador

    def usar_unidad(self):
        self._unidades -= 1


class SegundoTurno:

    def __init__(self, jugador):
        self._jugador = jugador
        self._unidades = 3

    def jugador_actual(self):
        return self._jugador

    def usar_unidad(self):
        self._unidades -= 1


class PrimerTurno:

    def __init__(self, jugador):
        self._jugador = jugador
        self._unidades = 6

    def jugador_actual(self):
        return self._jugador

    def usar_unidad(self):
        self._unidades -= 1