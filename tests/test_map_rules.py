"""Tests de reglas de mapa en la GUI."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui.mapa.map_rules import son_adyacentes


class MapRulesTests(unittest.TestCase):
    """Pruebas de adyacencia desde TOML."""

    def test_son_adyacentes_en_tema_test(self) -> None:
        self.assertTrue(son_adyacentes("test", "Circulo", "Rectangulo"))
        self.assertTrue(son_adyacentes("test", "Rectangulo", "Circulo"))

    def test_no_adyacentes_paises_lejanos(self) -> None:
        self.assertFalse(son_adyacentes("classic", "Argentina", "China"))


if __name__ == "__main__":
    unittest.main()
