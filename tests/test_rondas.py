
import unittest

from src.rondas import PrimeraRonda
#from src.mapa import Mapa

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


