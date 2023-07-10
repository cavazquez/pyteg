import unittest

from src.country import Country


class TestCountry(unittest.TestCase):
    def test_create_instance(self):
        self.assertTrue(Country('xyz'))

    def test_get_name(self):
        self.assertEqual(Country('Argentina').get_name(), 'Argentina')

