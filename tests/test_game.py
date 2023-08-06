import unittest

from src.game import Game
from src.mapa import Mapa
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class TestGame(unittest.TestCase):
    def test_create_instance(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        self.assertTrue(game)
        self.assertFalse(game.empezo())
        self.assertIsInstance(game.turnos()[0], PrimerTurno)

    def test_cant_jugadores(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        self.assertEqual(game.cant_jugadores(), 1)

    def test_agregar_jugador(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        self.assertEqual(game.jugadores(), {1: "Fulano"})

    def test_lista_jugadores(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        self.assertListEqual(game.lista_jugadores(), ["Fulano"])

    def test_empezar(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        game.agregar_jugador(2, "Mengano")
        game.empezar()
        self.assertIsInstance(game.turnos()[0], PrimerTurno)
        self.assertIsInstance(game.turnos()[1], PrimerTurno)

    def test_finalizar_turno(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        game.agregar_jugador(2, "Mengano")
        game.empezar()
        game.finalizar_turno()
        self.assertEqual(game.turno_actual(), 1)

    def test_finalizar_turno_y_primer_ronda(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        game.agregar_jugador(2, "Mengano")
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SegundoTurno)
        self.assertIsInstance(game.turnos()[1], SegundoTurno)

    def test_finalizar_turno_y_segunda_ronda(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        game.agregar_jugador(2, "Mengano")
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SiguientesTurnos)
        self.assertIsInstance(game.turnos()[1], SiguientesTurnos)

    def test_finalizar_turno_y_tercer_ronda(self):
        mapa = Mapa(lambda: None)
        game = Game(mapa, None)
        game.agregar_jugador(1, "Fulano")
        game.agregar_jugador(2, "Mengano")
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()

        turno1 = game.turnos()[0]
        turno2 = game.turnos()[1]
        game.finalizar_turno()
        game.finalizar_turno()
        self.assertNotEqual(game.turnos()[0], turno1)
        self.assertNotEqual(game.turnos()[1], turno2)
