import unittest

from src.game import Game, build_tarjetas_de_paises
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


    def test_cantidad_tarjetas_de_paises(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }
        mapa = Mapa(build_mapa)
        simbolos = ["Galeon", "Globo"]
        tarjetas = build_tarjetas_de_paises(mapa, simbolos)
        game = Game(mapa, tarjetas)
        self.assertEqual(len(game.tarjetas_de_paises()), 3)

    def test_cada_tarjeta_es_un_pais(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }
        mapa = Mapa(build_mapa)
        simbolos = ["Galeon", "Globo"]
        tarjetas = build_tarjetas_de_paises(mapa, simbolos)
        game = Game(mapa, tarjetas)
        self.assertTrue(all(
            [ tarjeta.dame_pais() in mapa.paises() 
                for tarjeta in game.tarjetas_de_paises() ]))


    def test_cada_pais_tiene_una_tarjeta(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }
        mapa = Mapa(build_mapa)
        simbolos = ["Galeon", "Globo"]
        tarjetas = build_tarjetas_de_paises(mapa, simbolos)
        game = Game(mapa, tarjetas)
        paises_en_tarjetas = [ tarjeta.dame_pais()
                for tarjeta in game.tarjetas_de_paises()]
        self.assertTrue(all(
            [ pais in paises_en_tarjetas for pais in mapa.paises() ]))


    def test_cada_tarjeta_tiene_un_simbolo(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }
        mapa = Mapa(build_mapa)
        simbolos = ["Galeon", "Globo"]
        tarjetas = build_tarjetas_de_paises(mapa, simbolos)
        game = Game(mapa, tarjetas)
        self.assertTrue(all(
            [ tarjeta.dame_simbolo() in simbolos 
                for tarjeta in game.tarjetas_de_paises() ]))


    def test_simbolos_alternados(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }
        mapa = Mapa(build_mapa)
        simbolos = ["Galeon", "Globo"]
        tarjetas = build_tarjetas_de_paises(mapa, simbolos)
        self.assertEqual(tarjetas[0].dame_simbolo(), "Galeon")
        self.assertEqual(tarjetas[1].dame_simbolo(), "Globo")
        self.assertEqual(tarjetas[2].dame_simbolo(), "Galeon")

