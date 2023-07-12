
import unittest

from src.rondas import PrimeraRonda, SegundaRonda, SiguientesRondas
from src.mapa import Mapa

class TestPrimeraRonda(unittest.TestCase):

    def test_jugadores(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        self.assertListEqual(ronda.jugadores(), ["Fulano","Mengano"])

    def test_cantidad_turnos(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        self.assertEqual(len(ronda.turnos()), 2)

    def test_turno_actual(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[0])

    def test_finalizar_turno(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[1])


    def test_sin_turnos(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        ronda.finalizar_turno()
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), None)

    def test_usar_unidad(self):
        ronda = PrimeraRonda(["Fulano","Mengano"])
        ronda.usar_unidad()

class TestSegundaRonda(unittest.TestCase):

    def test_jugadores(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        self.assertListEqual(ronda.jugadores(), ["Fulano","Mengano"])

    def test_cantidad_turnos(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        self.assertEqual(len(ronda.turnos()), 2)

    def test_turno_actual(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[0])

    def test_finalizar_turno(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[1])


    def test_sin_turnos(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        ronda.finalizar_turno()
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), None)

    def test_usar_unidad(self):
        ronda = SegundaRonda(["Fulano","Mengano"])
        ronda.usar_unidad()


class TestSiguientesRondas(unittest.TestCase):

    def test_jugadores(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        self.assertListEqual(ronda.jugadores(), ["Fulano","Mengano"])

    def test_cantidad_turnos(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        self.assertEqual(len(ronda.turnos()), 2)

    def test_turno_actual(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[0])

    def test_finalizar_turno(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), ronda.turnos()[1])


    def test_sin_turnos(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        ronda.finalizar_turno()
        ronda.finalizar_turno()
        self.assertEqual(ronda.turno_actual(), None)

    def test_usar_unidad(self):
        def build_mapa():
            return {}
        mapa = Mapa(build_mapa)
        ronda = SiguientesRondas(["Fulano","Mengano"], mapa)
        ronda.usar_unidad()


