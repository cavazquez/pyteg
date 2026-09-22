"""Pruebas de dados y alcance de misiles de Revancha."""

from __future__ import annotations

import random
import unittest
from typing import TYPE_CHECKING, cast

from pyteg.core.cartas.mazo import Mazo
from pyteg.core.partida.reglas import load_theme_rules
from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.model import SituationCard
from pyteg.core.situaciones.runtime import SituationRuntime
from pyteg.server.juego.game import Game
from pyteg.server.juego.mapa import Mapa

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol
    from pyteg.server.app import Server


class _Player:
    def __init__(self, userid: int) -> None:
        self._userid = userid

    def userid(self) -> int:
        return self._userid

    def username(self) -> str:
        return f"Jugador{self._userid}"

    def color_actual(self) -> None:
        return None


class _Server:
    def finalizar_partida(self) -> bool:
        return True

    def enviar_sistema(self, _message: str) -> None:
        pass

    def enviar_colores_asignados(self) -> None:
        pass


def _combat_map() -> Mapa:
    """Construye dos países con unidades suficientes para no conquistar.

    Returns:
        Mapa de combate mínimo.

    """

    def build() -> dict[str, list[int | str | list[str] | None]]:
        return {
            "A": [100, "left", 1, ["B"]],
            "B": [100, "right", 2, ["A"]],
        }

    return Mapa(build)


def _missile_map() -> Mapa:
    """Construye una cadena para comprobar distancias 1, 2 y 3.

    Returns:
        Mapa lineal con cuatro países.

    """

    def build() -> dict[str, list[int | str | list[str] | None]]:
        return {
            "A": [1, "left", 1, ["B"]],
            "B": [1, "left", 1, ["A", "C"]],
            "C": [1, "right", 2, ["B", "D"]],
            "D": [1, "right", 2, ["C"]],
        }

    return Mapa(build, load_theme_rules("revancha"))


class RevanchaCombatTests(unittest.TestCase):
    """Contrato de combate normal, situación y alcance de misiles."""

    def test_viento_a_favor_permite_cuatro_dados(self) -> None:
        """La situación aumenta el ataque de tres a cuatro dados."""
        mapa = _combat_map()
        runtime = SituationRuntime(
            mapa,
            SituationDeck(
                [SituationCard("wind", "Viento", "tailwind")],
                rng=random.Random(1),  # noqa: S311
            ),
        )
        runtime.begin_round(2, (1, 2), {})
        game = Game(
            mapa,
            Mazo(mapa.paises(), ["Soldado"]),
            cast("list[IClientProtocol]", [_Player(1), _Player(2)]),
            cast("Server", _Server()),
            situation_runtime=runtime,
            rules=load_theme_rules("revancha"),
            dice_rng=random.Random(7),  # noqa: S311
        )

        result = game.atacar("A", "B")

        self.assertEqual(len(result["dados_atacante"]), 4)
        self.assertEqual(len(result["dados_defensor"]), 3)

    def test_dados_inyectados_reproducen_el_combate(self) -> None:
        """Dos partidas con la misma fuente producen el mismo resultado."""
        results = []
        for _ in range(2):
            mapa = _combat_map()
            game = Game(
                mapa,
                Mazo(mapa.paises(), ["Soldado"]),
                cast("list[IClientProtocol]", [_Player(1), _Player(2)]),
                cast("Server", _Server()),
                rules=load_theme_rules("revancha"),
                dice_rng=random.Random(11),  # noqa: S311
            )
            results.append(game.atacar("A", "B"))

        self.assertEqual(results[0]["dados_atacante"], results[1]["dados_atacante"])
        self.assertEqual(results[0]["dados_defensor"], results[1]["dados_defensor"])

    def test_misiles_calculan_dano_3_2_1_por_distancia(self) -> None:
        """El grafo activo determina el daño a una, dos y tres fronteras."""
        mapa = _missile_map()

        self.assertEqual(mapa.calcular_distancia("A", "B"), 1)
        self.assertEqual(mapa.calcular_distancia("A", "C"), 2)
        self.assertEqual(mapa.calcular_distancia("A", "D"), 3)
        self.assertEqual(mapa.calcular_dano_misil(1), 3)
        self.assertEqual(mapa.calcular_dano_misil(2), 2)
        self.assertEqual(mapa.calcular_dano_misil(3), 1)
        self.assertEqual(mapa.calcular_dano_misil(4), 0)


if __name__ == "__main__":
    unittest.main()
