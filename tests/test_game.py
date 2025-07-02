import unittest

from src.game import Game
from src.mapa import Mapa
from src.mazo import Mazo
from src.server import Server
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class TestGame(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.server = Server()
        self.mapa = Mapa(lambda: None)
        self.default_jugadores = ["Fulano", "Mengano"]

    def test_create_instance(self):
        game = Game(self.mapa, None, None, self.server)
        self.assertTrue(game)
        self.assertFalse(game.empezo())
        self.assertIsInstance(game.turnos()[0], PrimerTurno)

    def test_cant_jugadores(self):
        game = Game(self.mapa, None, ["Fulano"], self.server)
        self.assertEqual(game.cant_jugadores(), 1)

    def test_agregar_jugador(self):
        game = Game(self.mapa, None, ["Fulano"], self.server)
        self.assertEqual(game.jugadores(), ["Fulano"])

    def test_lista_jugadores(self):
        game = Game(self.mapa, None, ["Fulano"], self.server)
        self.assertListEqual(game.lista_jugadores(), ["Fulano"])

    def test_empezar(self):
        game = Game(self.mapa, None, self.default_jugadores, self.server)
        game.empezar()
        self.assertIsInstance(game.turnos()[0], PrimerTurno)
        self.assertIsInstance(game.turnos()[1], PrimerTurno)

    def test_finalizar_turno(self):
        game = Game(self.mapa, None, self.default_jugadores, self.server)
        game.empezar()
        game.finalizar_turno()
        self.assertEqual(game.id_turno_actual(), 1)

    def test_finalizar_turno_y_primer_ronda(self):
        game = Game(self.mapa, None, self.default_jugadores, self.server)
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SegundoTurno)
        self.assertIsInstance(game.turnos()[1], SegundoTurno)

    def test_finalizar_turno_y_segunda_ronda(self):
        game = Game(self.mapa, None, self.default_jugadores, self.server)
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SiguientesTurnos)
        self.assertIsInstance(game.turnos()[1], SiguientesTurnos)

    def test_finalizar_turno_y_tercer_ronda(self):
        game = Game(self.mapa, None, self.default_jugadores, self.server)
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

    def test_canje_tarjeta(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_segundo_canje(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 7)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_tercer_canje(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 10)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_obtener_una_tarjeta(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        game.dame_una_tarjeta("Mengano")
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 1)

    def test_canje_defensivo_mismo_simbolo(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
                "Peru": [1, "America", None],
                "Brasil": [1, "America", None],
                "Mexico": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)

    def test_canje_defensivo_distinto_simbolo(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
                "Peru": [1, "America", None],
                "Brasil": [1, "America", None],
                "Mexico": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo", "Galeon", "Cañon"])
        game = Game(mapa, mazo, ["Mengano"], self.server)
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        game.dame_una_tarjeta("Mengano")
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 5)
        game.dame_una_tarjeta("Mengano")
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
