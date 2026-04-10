"""Tests para el módulo de batalla."""

import unittest

from pyteg.batalla import Batalla


class TestBatalla(unittest.TestCase):
    """Tests para la clase Batalla."""

    def test_calcular_dados_atacante_si_tengo_2(self) -> None:
        """Prueba calcular dados del atacante con 2 unidades."""
        self.assertEqual(Batalla.calcular_cant_dados_atacante(2), 1)

    def test_calcular_dados_atacante_si_tengo_4(self) -> None:
        """Prueba calcular dados del atacante con 4 unidades."""
        self.assertEqual(Batalla.calcular_cant_dados_atacante(4), 3)

    def test_calcular_dados_defensor_si_tengo_2(self) -> None:
        """Prueba calcular dados del defensor con 2 unidades."""
        self.assertEqual(Batalla.calcular_cant_dados_defensor(2), 2)

    def test_calcular_dados_defensor_si_tengo_4(self) -> None:
        """Prueba calcular dados del defensor con 4 unidades."""
        self.assertEqual(Batalla.calcular_cant_dados_atacante(4), 3)

    def test_batalla_donde_siempre_gana_atacante(self) -> None:
        """Prueba una batalla donde siempre gana el atacante."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [4, 3, 2], [3, 2, 1])
        self.assertCountEqual(resultado["restar"], ["Uruguay", "Uruguay", "Uruguay"])

    def test_batalla_donde_siempre_gana_defensor(self) -> None:
        """Prueba una batalla donde siempre gana el defensor."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [3, 2, 1], [4, 3, 2])
        self.assertCountEqual(
            resultado["restar"],
            ["Argentina", "Argentina", "Argentina"],
        )
        self.assertEqual(resultado["atacante"], "Argentina")
        self.assertEqual(resultado["defensor"], "Uruguay")

    def test_batalla_donde_siempre_empatan(self) -> None:
        """Prueba una batalla donde siempre empatan los dados."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [3, 3, 3], [3, 3, 3])
        self.assertCountEqual(
            resultado["restar"],
            ["Argentina", "Argentina", "Argentina"],
        )
        self.assertEqual(resultado["atacante"], "Argentina")
        self.assertEqual(resultado["defensor"], "Uruguay")

    def test_batalla_atacan_2(self) -> None:
        """Prueba una batalla donde el atacante usa 2 dados."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [3, 2], [4, 3, 2])
        self.assertCountEqual(resultado["restar"], ["Argentina", "Argentina"])

    def test_batalla_defiende_2(self) -> None:
        """Prueba una batalla donde el defensor usa 2 dados."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [4, 3, 2], [3, 2])
        self.assertCountEqual(resultado["restar"], ["Uruguay", "Uruguay"])

    def test_batalla_uno_y_uno(self) -> None:
        """Prueba una batalla donde ambos pierden una unidad."""
        resultado = Batalla.ataquen("Argentina", "Uruguay", [6, 3, 2], [5, 4])
        self.assertCountEqual(resultado["restar"], ["Argentina", "Uruguay"])
