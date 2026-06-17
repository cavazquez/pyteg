"""Tests de la tarea del servidor: canjear tres tarjetas."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, TypeVar, cast

from pyteg.core.cartas.mazo import Mazo
from pyteg.server.juego.estado import Estado
from pyteg.server.juego.game import Game
from pyteg.server.juego.mapa import Mapa
from pyteg.server.juego.state_validator import ServerStateValidator
from pyteg.server.tasks.cards_missiles.canjear_tarjetas import ServerTaskCanjearTarjetas
from tests.test_game import FakePlayer

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.protocols import IClientProtocol
    from pyteg.server.app import Server
    from pyteg.server.tasks.types import CanjearTarjetasTaskData

T = TypeVar("T")


def _no_none(value: T | None) -> T:
    """Devuelve `value` si no es `None`.

    Returns:
        El valor recibido cuando no es `None`.

    Raises:
        AssertionError: si `value` es `None`.

    """
    if value is None:
        msg = "Se esperaba un valor no nulo"
        raise AssertionError(msg)
    return value


def _tres_tarjetas(mazo: Mazo, jugador: FakePlayer) -> list[TarjetaDePais]:
    """Asigna tres tarjetas al jugador para el canje.

    Returns:
        Lista de tres tarjetas no nulas.

    """
    return [_no_none(mazo.asignar_tarjeta(jugador)) for _ in range(3)]


def _mapa_minimo() -> Mapa:
    """Mapa mínimo para tests de canje de tarjetas.

    Returns:
        Instancia de `Mapa` con tres países.

    """

    def build() -> dict[str, list[int | str | list[str] | None]]:
        return {
            "Argentina": [4, "Africa", None],
            "Uruguay": [2, "Africa", None],
            "Chile": [1, "America", None],
        }

    return Mapa(build)


class _FakeServer:
    """Servidor mínimo con `Game` real para tareas de tarjetas."""

    def __init__(self, game: Game | None, mapa: Mapa) -> None:
        self.mapa = mapa
        self.game = game
        self.estado = Estado()
        self.estado.esperar_jugadores()
        self.estado.empezar_partida()
        self.tarjetas_enviadas: list[object] = []
        self.unidades_enviadas = False

    def enviar_tarjetas_jugador(self, client: object) -> None:
        self.tarjetas_enviadas.append(client)

    def enviar_unidades_disponibles(self) -> None:
        self.unidades_enviadas = True


class TestServerTaskCanjearTarjetas(unittest.TestCase):
    """Canje triple de tarjetas por unidades generales."""

    def setUp(self) -> None:
        """Jugador 1 con partida iniciada y tres tarjetas asignadas."""
        self.mapa = _mapa_minimo()
        self.mazo = Mazo(self.mapa.paises(), ["Globo"])
        self.server = _FakeServer(None, self.mapa)
        self.jugador = FakePlayer(1, "Mengano", cast("Server", self.server))
        self.game = Game(
            self.mapa, self.mazo, [self.jugador], cast("Server", self.server)
        )
        self.server.game = self.game
        self.game.empezar()
        self.client = self.jugador
        self.tarjetas = _tres_tarjetas(self.mazo, self.jugador)

    def _run_canjear(self, payload: CanjearTarjetasTaskData) -> None:
        task = ServerTaskCanjearTarjetas(payload)
        task._validator = ServerStateValidator()  # noqa: SLF001
        task.run(cast("IClientProtocol", self.client))

    def test_canje_exitoso_tres_mismo_simbolo(self) -> None:
        """Un canje válido consume las tarjetas y suma unidades."""
        turno_actual = self.game.turno_actual()
        unidades_antes = turno_actual.cant_unidades()
        payload: CanjearTarjetasTaskData = {
            "mensaje": "canjear_tarjetas",
            "tarjetas": [{"pais": t.pais, "simbolo": t.simbolo} for t in self.tarjetas],
        }

        self._run_canjear(payload)

        self.assertEqual(turno_actual.cant_unidades(), unidades_antes + 4)
        self.assertEqual(self.mazo.cant_tarjetas_asignadas(self.jugador), 0)
        cast("MagicMock", self.client.transmisor).enviar_sistema.assert_called_once()
        self.assertTrue(self.server.unidades_enviadas)
        self.assertEqual(len(self.server.tarjetas_enviadas), 1)

    def test_canje_rechazado_si_tarjeta_no_pertenece_al_jugador(self) -> None:
        """Tarjeta ajena produce error de chat."""
        payload: CanjearTarjetasTaskData = {
            "mensaje": "canjear_tarjetas",
            "tarjetas": [{"pais": "Inexistente", "simbolo": "Globo"}],
        }

        self._run_canjear(payload)

        cast("MagicMock", self.client.transmisor).enviar_error_chat.assert_called_once()
        self.assertEqual(self.mazo.cant_tarjetas_asignadas(self.jugador), 3)


if __name__ == "__main__":
    unittest.main()
