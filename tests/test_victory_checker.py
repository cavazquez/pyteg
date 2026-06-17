"""Tests para VictoryChecker."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from pyteg.core.partida.victory_checker import VictoryChecker
from pyteg.server.juego.mapa import Mapa

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class _Jugador:
    """Jugador mínimo conforme a IClientProtocol para tests."""

    def __init__(self, user_id: int, username: str) -> None:
        self._user_id = user_id
        self._username = username

    def userid(self) -> int:
        return self._user_id

    def username(self) -> str:
        return self._username


def _mapa_tres_paises() -> Mapa:
    """Mapa con tres países: dos de jugador 1 y uno de jugador 2.

    Returns:
        Instancia de `Mapa` para tests de victoria.

    """

    def build() -> dict[str, list[int | str | list[str] | None]]:
        return {
            "Argentina": [1, "America", 1],
            "Brasil": [1, "America", 1],
            "Chile": [1, "America", 2],
        }

    return Mapa(build)


def _jugadores(*items: _Jugador) -> list[IClientProtocol]:
    """Convierte jugadores de test al tipo esperado por VictoryChecker.

    Returns:
        Lista tipada para `verificar_condicion_victoria`.

    """
    return cast("list[IClientProtocol]", list(items))


class TestVictoryChecker(unittest.TestCase):
    """Comprueba condiciones de victoria por países y objetivos secretos."""

    def test_mapa_vacio_sin_ganador(self) -> None:
        """Sin países en el mapa no puede haber ganador."""
        mapa = Mapa(dict)
        checker = VictoryChecker(mapa, paises_para_victoria=1)
        jugadores = _jugadores(_Jugador(1, "A"))

        self.assertIsNone(checker.verificar_condicion_victoria(jugadores))

    def test_sin_ganador_por_paises(self) -> None:
        """Nadie alcanza el umbral configurado."""
        mapa = _mapa_tres_paises()
        checker = VictoryChecker(mapa, paises_para_victoria=3)
        jugadores = _jugadores(_Jugador(1, "Fulano"), _Jugador(2, "Mengano"))

        self.assertIsNone(checker.verificar_condicion_victoria(jugadores))

    def test_victoria_por_umbral_de_paises(self) -> None:
        """Gana quien controla al menos `paises_para_victoria`."""
        mapa = _mapa_tres_paises()
        checker = VictoryChecker(mapa, paises_para_victoria=2)
        jugadores = _jugadores(_Jugador(1, "Fulano"), _Jugador(2, "Mengano"))

        ganador = checker.verificar_condicion_victoria(jugadores)

        self.assertIsNotNone(ganador)
        if ganador is None:
            self.fail("Se esperaba un ganador por umbral de países")
        self.assertIs(ganador, jugadores[0])
        self.assertEqual(ganador.userid(), 1)

    def test_victoria_controlando_todos_los_paises(self) -> None:
        """Con umbral 0, hay que controlar todos los países del mapa."""

        def build() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "America", 1],
                "Brasil": [1, "America", 1],
                "Chile": [1, "America", 1],
            }

        mapa = Mapa(build)
        checker = VictoryChecker(mapa, paises_para_victoria=0)
        jugadores = _jugadores(_Jugador(1, "Fulano"))

        ganador = checker.verificar_condicion_victoria(jugadores)

        self.assertIs(ganador, jugadores[0])

    def test_objetivo_secreto_tiene_prioridad(self) -> None:
        """Si objetivos secretos están activos, se evalúan antes que países."""
        mapa = _mapa_tres_paises()
        objetivos = MagicMock()
        objetivos.verificar_condicion_victoria.return_value = True
        objetivos.get_objetivo_jugador.return_value = {
            "descripcion": "Conquistar Asia",
        }
        color_manager = MagicMock()
        checker = VictoryChecker(
            mapa,
            paises_para_victoria=2,
            objetivos_secretos=objetivos,
            objetivos_secretos_activados=True,
            color_manager=color_manager,
        )
        jugadores = _jugadores(_Jugador(2, "Mengano"), _Jugador(1, "Fulano"))

        ganador = checker.verificar_condicion_victoria(jugadores)

        self.assertIs(ganador, jugadores[0])
        objetivos.verificar_condicion_victoria.assert_called()

    def test_objetivos_secretos_inactivos_usa_paises(self) -> None:
        """Con flag desactivado se ignora el gestor de objetivos."""
        mapa = _mapa_tres_paises()
        objetivos = MagicMock()
        objetivos.verificar_condicion_victoria.return_value = True
        checker = VictoryChecker(
            mapa,
            paises_para_victoria=2,
            objetivos_secretos=objetivos,
            objetivos_secretos_activados=False,
            color_manager=MagicMock(),
        )
        jugadores = _jugadores(_Jugador(1, "Fulano"))

        ganador = checker.verificar_condicion_victoria(jugadores)

        self.assertIs(ganador, jugadores[0])
        objetivos.verificar_condicion_victoria.assert_not_called()

    def test_objetivos_secretos_sin_color_manager(self) -> None:
        """Sin color_manager no se evalúan objetivos aunque estén activados."""
        mapa = _mapa_tres_paises()
        objetivos = MagicMock()
        checker = VictoryChecker(
            mapa,
            paises_para_victoria=2,
            objetivos_secretos=objetivos,
            objetivos_secretos_activados=True,
            color_manager=None,
        )
        jugadores = _jugadores(_Jugador(1, "Fulano"))

        ganador = checker.verificar_condicion_victoria(jugadores)

        self.assertIs(ganador, jugadores[0])
        objetivos.verificar_condicion_victoria.assert_not_called()


if __name__ == "__main__":
    unittest.main()
