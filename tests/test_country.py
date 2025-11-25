import unittest

from src.country import Country


class TestCountry(unittest.TestCase):
    def test_create_instance(self) -> None:
        self.assertTrue(Country("xyz"))

    def test_get_name(self) -> None:
        self.assertEqual(Country("Argentina").get_name(), "Argentina")
