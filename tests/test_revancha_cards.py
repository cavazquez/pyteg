"""Pruebas del mazo y los canjes específicos de Revancha."""

from __future__ import annotations

import unittest
from typing import ClassVar

from pyteg.core.cartas.canje import seleccion_valida
from pyteg.core.cartas.mazo import Mazo
from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
from pyteg.core.partida.card_manager import CardManager
from pyteg.core.partida.reglas import ThemeRules, load_theme_rules
from pyteg.toml_reader import TomlReader


class _Turn:
    def __init__(self) -> None:
        self.unidades = 0

    def agregar_unidades_generales(self, cantidad: int) -> None:
        self.unidades += cantidad


class _TurnManager:
    def __init__(self) -> None:
        self.ronda = 1
        self.turno = 1
        self.actual = _Turn()

    def turno_actual(self) -> _Turn:
        return self.actual

    def num_ronda(self) -> int:
        return self.ronda

    def id_turno_actual(self) -> int:
        return self.turno

    def clave_turno(self) -> tuple[int, int]:
        return self.ronda, self.turno


class TestRevanchaCards(unittest.TestCase):
    """Contrato de cartas, equivalencias y progresión de canjes."""

    reader: ClassVar[TomlReader]
    rules: ClassVar[ThemeRules]

    @classmethod
    def setUpClass(cls) -> None:
        """Carga el mapa y las reglas estrictas de Revancha."""
        cls.reader = TomlReader.from_theme("revancha", strict=True)
        cls.rules = load_theme_rules("revancha")

    def test_distribucion_crea_72_paises_y_7_continentes(self) -> None:
        """El mazo separa cartas de país y cartas de continente."""
        distribution = self.reader.get_cartas_distribucion()
        self.assertEqual(len(distribution["paises"]), 72)
        self.assertEqual(len(distribution["continentes"]), 7)
        self.assertEqual(distribution["especiales"], {})

        extras = [
            (f"continente:{continent}", symbol, "continente", continent)
            for continent, symbol in distribution["continentes"].items()
        ]
        mazo = Mazo(
            self.reader.todos_los_paises(),
            self.reader.get_simbolos(),
            simbolos_por_pais=distribution["paises"],
            cartas_extra=extras,
        )
        self.assertEqual(len(mazo.tarjetas_por_tipo("pais")), 72)
        self.assertEqual(len(mazo.tarjetas_por_tipo("continente")), 7)
        self.assertEqual(mazo.cantidad_tarjetas(), 79)

    def test_reinicio_recrea_cartas_extra_sin_asignaciones(self) -> None:
        """Reiniciar elimina asignaciones también de cartas de continente."""
        distribution = self.reader.get_cartas_distribucion()
        extras = [
            (f"continente:{continent}", symbol, "continente", continent)
            for continent, symbol in distribution["continentes"].items()
        ]
        mazo = Mazo(
            self.reader.todos_los_paises(),
            self.reader.get_simbolos(),
            simbolos_por_pais=distribution["paises"],
            cartas_extra=extras,
        )
        card = mazo.asignar_tarjeta(7, tipo="continente", continente="Asia")
        self.assertIsNotNone(card)
        self.assertEqual(mazo.cant_tarjetas_asignadas(7), 1)

        mazo.reiniciar()

        self.assertEqual(mazo.cant_tarjetas_asignadas(7), 0)
        self.assertEqual(len(mazo.tarjetas_por_tipo("continente")), 7)

    def test_equivalencias_homogeneas_distintas_continentales_y_super(self) -> None:
        """El validador acepta las equivalencias oficiales y rechaza incompletas."""
        equivalencias = self.rules.continent_card_exchange_map
        self.assertTrue(
            seleccion_valida(
                [TarjetaDePais(str(i), "Avion") for i in range(3)],
            )
        )
        self.assertTrue(
            seleccion_valida([
                TarjetaDePais("a", "Avion"),
                TarjetaDePais("b", "Tanque"),
                TarjetaDePais("c", "Soldado"),
            ])
        )
        self.assertTrue(
            seleccion_valida(
                [
                    TarjetaDePais(
                        "c", "Continente", tipo="continente", continente="Asia"
                    )
                ],
                equivalencias=equivalencias,
            )
        )
        self.assertTrue(
            seleccion_valida(
                [
                    TarjetaDePais(
                        "c",
                        "Continente",
                        tipo="continente",
                        continente="AmericaDelSur",
                    ),
                    TarjetaDePais("p", "Soldado"),
                ],
                equivalencias=equivalencias,
            )
        )
        self.assertTrue(seleccion_valida([TarjetaDePais("p", "Supertarjeta")]))
        self.assertFalse(
            seleccion_valida([
                TarjetaDePais("a", "Avion"),
                TarjetaDePais("b", "Tanque"),
            ])
        )

    def test_primer_segundo_y_tercer_canje_y_uno_por_turno(self) -> None:
        """La progresión es 6/10/15 y el turno sólo permite un canje."""
        mazo = Mazo([f"P{i}" for i in range(9)], ["Avion"])
        manager = _TurnManager()
        cards = CardManager(mazo, manager, rules=self.rules)
        cards.inicializar_canjes([7])
        selected = [mazo.asignar_tarjeta(7) for _ in range(3)]
        valid = [card for card in selected if card is not None]

        cards.canjear(7, valid)
        self.assertEqual(cards.cant_canjes(7), 1)
        self.assertEqual(manager.actual.unidades, 6)
        self.assertFalse(cards.puede_canjear_en_turno(7))

        manager.turno += 1
        manager.actual = _Turn()
        self.assertTrue(cards.puede_canjear_en_turno(7))
        selected = [mazo.asignar_tarjeta(7) for _ in range(3)]
        cards.canjear(7, [card for card in selected if card is not None])
        self.assertEqual(cards.cant_canjes(7), 2)
        self.assertEqual(manager.actual.unidades, 10)

        manager.turno += 1
        manager.actual = _Turn()
        selected = [mazo.asignar_tarjeta(7) for _ in range(3)]
        cards.canjear(7, [card for card in selected if card is not None])
        self.assertEqual(cards.cant_canjes(7), 3)
        self.assertEqual(manager.actual.unidades, 15)


if __name__ == "__main__":
    unittest.main()
