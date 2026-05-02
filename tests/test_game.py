"""Tests para el módulo de juego del servidor."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, TypeVar, cast
from unittest.mock import MagicMock

from pyteg.core.cartas.mazo import Mazo
from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from pyteg.server.app import Server
from pyteg.server.juego.game import Game
from pyteg.server.juego.mapa import Mapa

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.protocols.server import ServerLikeProtocol
    from pyteg.server.conexion.transmisor import ServerTransmisor

T = TypeVar("T")


def _no_none(value: T | None) -> T:
    """Devuelve `value` si no es `None`, levantando si lo es.

    Helper de estrechamiento de tipo para tests: evita `cast` y `assert`
    inline sin perder el chequeo en runtime.

    Returns:
        El valor recibido cuando no es `None`.

    Raises:
        AssertionError: si `value` es `None`.

    """
    if value is None:
        msg = "Se esperaba un valor no nulo"
        raise AssertionError(msg)
    return value


class FakePlayer:
    """Sustituto mínimo de `Client` para tests de `Game` y `Mazo`.

    Cumple estructuralmente con `IClientProtocol`: expone `userid()`,
    `username()`, mutadores y propiedades dummy, suficientes para que
    `Game` y `CardManager` lo acepten sin `cast`.
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        server: Server | None = None,
    ) -> None:
        """Crea un jugador falso con `userid` y nombre."""
        self._user_id = user_id
        self._username = username
        self._color: IColor | None = None
        self._server: ServerLikeProtocol = cast("ServerLikeProtocol", server)
        self._transmisor: ServerTransmisor = cast("ServerTransmisor", MagicMock())

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

    def set_username(self, username: str) -> None:
        """Cambia el nombre de usuario del jugador falso."""
        self._username = username

    def cambiar_color(self, color: str) -> None:
        """No-op: los tests no necesitan el color."""

    def asignar_color(self, color: IColor | None) -> None:
        """Guarda el color asignado para que `color_actual` lo devuelva."""
        self._color = color

    def color_actual(self) -> IColor | None:
        """Devuelve el color asignado, si lo hay.

        Returns:
            Color asignado o `None`.

        """
        return self._color

    @property
    def transmisor(self) -> ServerTransmisor:
        """Transmisor dummy (mock) compatible con `IClientProtocol`.

        Returns:
            Mock tipado estructuralmente como `ServerTransmisor`.

        """
        return self._transmisor

    @property
    def server(self) -> ServerLikeProtocol:
        """Servidor dummy compatible con `IClientProtocol`.

        Returns:
            Servidor inyectado en el constructor (puede ser un mock).

        """
        return self._server

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
            [],
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
            [jugador],
            self.server,
        )
        self.assertEqual(game.cant_jugadores(), 1)

    def test_agregar_jugador(self) -> None:
        """Prueba agregar un jugador al juego."""
        jugador = FakePlayer(1, "Uno", self.server)
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            [jugador],
            self.server,
        )
        self.assertEqual(game.jugadores(), [jugador])

    def test_lista_jugadores(self) -> None:
        """Prueba obtener la lista de jugadores."""
        jugador = FakePlayer(1, "Uno", self.server)
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            [jugador],
            self.server,
        )
        self.assertListEqual(game.lista_jugadores(), [jugador])

    def test_empezar(self) -> None:
        """Prueba empezar el juego."""
        game = Game(
            self.mapa,
            self.mazo_placeholder,
            self.default_jugadores,
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
            self.default_jugadores,
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
            self.default_jugadores,
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
            self.default_jugadores,
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
            self.default_jugadores,
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
            [jugador],
            self.server,
        )
        game.empezar()

        tarjetas = self._tres_tarjetas(mazo, jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()
        game.canjear(jugador, tarjetas)

        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 0)

    @staticmethod
    def _tres_tarjetas(mazo: Mazo, jugador: FakePlayer) -> list[TarjetaDePais]:
        """Asigna y devuelve 3 tarjetas (no `None`) para canjear en un test.

        Returns:
            Lista de tres tarjetas asignadas al jugador.

        """
        return [_no_none(mazo.asignar_tarjeta(jugador)) for _ in range(3)]

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
            [jugador],
            self.server,
        )
        game.empezar()

        game.canjear(jugador, self._tres_tarjetas(mazo, jugador))
        tarjetas = self._tres_tarjetas(mazo, jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear(jugador, tarjetas)

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
            [jugador],
            self.server,
        )
        game.empezar()

        for _ in range(2):
            game.canjear(jugador, self._tres_tarjetas(mazo, jugador))
        tarjetas = self._tres_tarjetas(mazo, jugador)
        turno_actual = game.turno_actual()

        cant_unidades = turno_actual.cant_unidades()

        game.canjear(jugador, tarjetas)

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
            [jugador],
            self.server,
        )
        game.empezar()

        game.dame_una_tarjeta(jugador)
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
            [jugador],
            self.server,
        )
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        for _ in range(6):
            game.dame_una_tarjeta(jugador)
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
            [jugador],
            self.server,
        )
        game.empezar()

        turno_actual = game.turno_actual()
        cant_unidades = turno_actual.cant_unidades()
        for _ in range(5):
            game.dame_una_tarjeta(jugador)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 5)
        game.dame_una_tarjeta(jugador)
        self.assertEqual(mazo.cant_tarjetas_asignadas(jugador), 3)
        self.assertEqual(turno_actual.cant_unidades(), cant_unidades + 4)
