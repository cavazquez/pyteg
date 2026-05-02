"""Tests para el módulo de juego del servidor."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, cast

from pyteg.core.cartas.mazo import Mazo
from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from pyteg.server.app import Server
from pyteg.server.juego.game import Game
from pyteg.server.juego.mapa import Mapa

if TYPE_CHECKING:
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.server.conexion.cliente import Client


class FakePlayer:
    """Sustituto mínimo de `Client` para tests de `Game` y `Mazo`."""

    def __init__(
        self,
        user_id: int,
        username: str,
        server: Server | None = None,
    ) -> None:
        """Crea un jugador falso con `userid` y nombre."""
        self._user_id = user_id
        self._username = username
        self.server = server

    def userid(self) -> int:
        """Devuelve el userid (int) del jugador falso.

        Returns:
            userid del jugador falso.

        """
        return self._user_id

    def username(self) -> str:
        """Devuelve el nombre de usuario del jugador falso.

        Returns:
            Nombre de usuario del jugador falso.

        """
        return self._username

    def __eq__(self, other: object) -> bool:
        """Compara jugadores falsos por `userid`.

        Returns:
            True si `other` es un `FakePlayer` con el mismo userid.

        """
        return isinstance(other, FakePlayer) and self._user_id == other._user_id

    def __hash__(self) -> int:
        """Hash estable basado en `userid`.

        Returns:
            Hash entero para usar el objeto en conjuntos/dicts.

        """
        return hash(self._user_id)


class TestGame(unittest.TestCase):
    """Tests para la clase Game."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.server = Server()
        self.mapa = Mapa(
            lambda: {
                "Argentina": [1, "America", None, ["Brasil"]],
                "Brasil": [1, "America", None, ["Argentina"]],
            }
        )
        self.default_jugadores = [
            FakePlayer(1, "Fulano", self.server),
            FakePlayer(2, "Mengano", self.server),
        ]
        self.mazo_placeholder = Mazo(self.mapa.paises(), ["Globo"])

    def test_create_instance(self) -> None:
        """Prueba crear una instancia de Game."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", []),
            self.server,
        )
        self.assertTrue(game)
        self.assertFalse(game.empezo())
        self.assertIsInstance(game.turnos()[0], PrimerTurno)

    def test_cant_jugadores(self) -> None:
        """Prueba contar jugadores."""
        jugador = FakePlayer(1, "Uno", self.server)
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", [jugador]),
            self.server,
        )
        self.assertEqual(game.cant_jugadores(), 1)

    def test_agregar_jugador(self) -> None:
        """Prueba agregar un jugador al juego."""
        jugador = FakePlayer(1, "Uno", self.server)
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", [jugador]),
            self.server,
        )
        self.assertEqual(game.jugadores(), [jugador])

    def test_lista_jugadores(self) -> None:
        """Prueba obtener la lista de jugadores."""
        jugador = FakePlayer(1, "Uno", self.server)
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", [jugador]),
            self.server,
        )
        self.assertListEqual(game.lista_jugadores(), [jugador])

    def test_empezar(self) -> None:
        """Prueba empezar el juego."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", self.default_jugadores),
            self.server,
        )
        game.empezar()
        self.assertIsInstance(game.turnos()[0], PrimerTurno)
        self.assertIsInstance(game.turnos()[1], PrimerTurno)

    def test_finalizar_turno(self) -> None:
        """Prueba finalizar un turno."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", self.default_jugadores),
            self.server,
        )
        game.empezar()
        game.finalizar_turno()
        self.assertEqual(game.id_turno_actual(), 1)

    def test_finalizar_turno_y_primer_ronda(self) -> None:
        """Prueba finalizar turnos y llegar a la primera ronda."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", self.default_jugadores),
            self.server,
        )
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SegundoTurno)
        self.assertIsInstance(game.turnos()[1], SegundoTurno)

    def test_finalizar_turno_y_segunda_ronda(self) -> None:
        """Prueba finalizar turnos y llegar a la segunda ronda."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", self.default_jugadores),
            self.server,
        )
        game.empezar()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()
        game.finalizar_turno()

        self.assertIsInstance(game.turnos()[0], SiguientesTurnos)
        self.assertIsInstance(game.turnos()[1], SiguientesTurnos)

    def test_finalizar_turno_y_tercer_ronda(self) -> None:
        """Prueba finalizar turnos y llegar a la tercera ronda."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            cast("list[Client]", self.default_jugadores),
            self.server,
        )
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
        """Prueba canjear tarjetas por primera vez."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        tarjeta1 = mazo.asignar_tarjeta(jugador)
        tarjeta2 = mazo.asignar_tarjeta(jugador)
        tarjeta3 = mazo.asignar_tarjeta(jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()
        self.assertIsNotNone(tarjeta1)
        self.assertIsNotNone(tarjeta2)
        self.assertIsNotNone(tarjeta3)
        game.canjear(
            cast("Client", jugador),
            [
                cast("TarjetaDePais", tarjeta1),
                cast("TarjetaDePais", tarjeta2),
                cast("TarjetaDePais", tarjeta3),
            ],
        )

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 0)

    def test_segundo_canje(self) -> None:
        """Prueba canjear tarjetas por segunda vez."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        t1 = mazo.asignar_tarjeta(jugador)
        t2 = mazo.asignar_tarjeta(jugador)
        t3 = mazo.asignar_tarjeta(jugador)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertIsNotNone(t3)
        game.canjear(
            cast("Client", jugador),
            [
                cast("TarjetaDePais", t1),
                cast("TarjetaDePais", t2),
                cast("TarjetaDePais", t3),
            ],
        )
        t1 = mazo.asignar_tarjeta(jugador)
        t2 = mazo.asignar_tarjeta(jugador)
        t3 = mazo.asignar_tarjeta(jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertIsNotNone(t3)
        game.canjear(
            cast("Client", jugador),
            [
                cast("TarjetaDePais", t1),
                cast("TarjetaDePais", t2),
                cast("TarjetaDePais", t3),
            ],
        )

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 7)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 0)

    def test_tercer_canje(self) -> None:
        """Prueba canjear tarjetas por tercera vez."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        for _ in range(2):
            t1 = mazo.asignar_tarjeta(jugador)
            t2 = mazo.asignar_tarjeta(jugador)
            t3 = mazo.asignar_tarjeta(jugador)
            self.assertIsNotNone(t1)
            self.assertIsNotNone(t2)
            self.assertIsNotNone(t3)
            game.canjear(
                cast("Client", jugador),
                [
                    cast("TarjetaDePais", t1),
                    cast("TarjetaDePais", t2),
                    cast("TarjetaDePais", t3),
                ],
            )
        t1 = mazo.asignar_tarjeta(jugador)
        t2 = mazo.asignar_tarjeta(jugador)
        t3 = mazo.asignar_tarjeta(jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertIsNotNone(t3)
        game.canjear(
            cast("Client", jugador),
            [
                cast("TarjetaDePais", t1),
                cast("TarjetaDePais", t2),
                cast("TarjetaDePais", t3),
            ],
        )

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 10)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 0)

    def test_obtener_una_tarjeta(self) -> None:
        """Prueba obtener una tarjeta del mazo."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", None],
                "Uruguay": [2, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mazo = Mazo(mapa.paises(), ["Globo"])
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        game.dame_una_tarjeta(cast("Client", jugador))
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 1)

    def test_canje_defensivo_mismo_simbolo(self) -> None:
        """Prueba canje defensivo automático con mismo símbolo."""

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
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        for _ in range(6):
            game.dame_una_tarjeta(cast("Client", jugador))
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)

    def test_canje_defensivo_distinto_simbolo(self) -> None:
        """Prueba canje defensivo automático con distintos símbolos."""

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
        jugador = FakePlayer(1, "Mengano", self.server)
        game = Game(
            mapa,
            mazo,
            cast("list[Client]", [jugador]),
            self.server,
        )
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        for _ in range(5):
            game.dame_una_tarjeta(cast("Client", jugador))
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 5)
        game.dame_una_tarjeta(cast("Client", jugador))
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
