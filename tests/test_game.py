import unittest

from src.mazo import Mazo
from src.server import Server
from src.server_game import Game
from src.server_mapa import Mapa
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class TestGame(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.server = Server()
        self.mapa = Mapa(
            lambda: {
                "Argentina": [1, "America", None, ["Brasil"]],
                "Brasil": [1, "America", None, ["Argentina"]],
            }
        )
        self.default_jugadores = ["Fulano", "Mengano"]

    def test_create_instance(self) -> None:
        game = Game(self.mapa, None, None, self.server)  # type: ignore[arg-type]
        self.assertTrue(game)
        self.assertFalse(game.empezo())
        self.assertIsInstance(game.turnos()[0], PrimerTurno)

    def test_cant_jugadores(self) -> None:
        game = Game(self.mapa, None, ["Fulano"], self.server)  # type: ignore[arg-type,list-item]
        self.assertEqual(game.cant_jugadores(), 1)

    def test_agregar_jugador(self) -> None:
        game = Game(self.mapa, None, ["Fulano"], self.server)  # type: ignore[arg-type,list-item]
        self.assertEqual(game.jugadores(), ["Fulano"])

    def test_lista_jugadores(self) -> None:
        game = Game(self.mapa, None, ["Fulano"], self.server)  # type: ignore[arg-type,list-item]
        self.assertListEqual(game.lista_jugadores(), ["Fulano"])

    def test_empezar(self) -> None:
        game = Game(self.mapa, None, self.default_jugadores, self.server)  # type: ignore[arg-type]
        game.empezar()
        self.assertIsInstance(game.turnos()[0], PrimerTurno)
        self.assertIsInstance(game.turnos()[1], PrimerTurno)

    def test_finalizar_turno(self) -> None:
        game = Game(self.mapa, None, self.default_jugadores, self.server)  # type: ignore[arg-type]
        game.empezar()
        game.finalizar_turno()
        self.assertEqual(game.id_turno_actual(), 1)

    def test_finalizar_turno_y_primer_ronda(self) -> None:
        game = Game(self.mapa, None, self.default_jugadores, self.server)  # type: ignore[arg-type]
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SegundoTurno)
        self.assertIsInstance(game.turnos()[1], SegundoTurno)

    def test_finalizar_turno_y_segunda_ronda(self) -> None:
        game = Game(self.mapa, None, self.default_jugadores, self.server)  # type: ignore[arg-type]
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SiguientesTurnos)
        self.assertIsInstance(game.turnos()[1], SiguientesTurnos)

    def test_finalizar_turno_y_tercer_ronda(self) -> None:
        game = Game(self.mapa, None, self.default_jugadores, self.server)  # type: ignore[arg-type]
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

    def test_canje_tarjeta(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_segundo_canje(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 7)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_tercer_canje(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]
        tarjeta1 = mazo.asignar_tarjeta("Mengano")
        tarjeta2 = mazo.asignar_tarjeta("Mengano")
        tarjeta3 = mazo.asignar_tarjeta("Mengano")
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear("Mengano", [tarjeta1, tarjeta2, tarjeta3])  # type: ignore[list-item]

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 10)
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 0)

    def test_obtener_una_tarjeta(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 1)

    def test_canje_defensivo_mismo_simbolo(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
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
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)

    def test_canje_defensivo_distinto_simbolo(self) -> None:
        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
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
        game = Game(mapa, mazo, ["Mengano"], self.server)  # type: ignore[list-item]
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 5)
        game.dame_una_tarjeta("Mengano")  # type: ignore[arg-type]
        self.assertEqual(mazo.cant_tarjetas_asignadas("Mengano"), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
