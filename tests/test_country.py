"""Tests para el módulo de país."""

import unittest

from src.country import Country


class TestCountry(unittest.TestCase):
    """Tests para la clase Country."""

    def test_create_instance(self) -> None:
        """Prueba crear una instancia de Country."""
        self.assertTrue(Country("xyz"))

    def test_get_name(self) -> None:
        """Prueba obtener el nombre del país."""
        self.assertEqual(Country("Argentina").get_name(), "Argentina")
