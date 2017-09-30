import unittest

from src.country import Country
from src.map import Map


class TestMap(unittest.TestCase):
    def test_creation_instance(self):
        self.assertTrue(Map({}, {}))

    def test_add_one_country(self):
        an_country = Country('Argentina')
        self.assertEqual(Map({an_country}, {}).get_countries(), {an_country})

    def test_countries_are_not_adjacent(self):
        an_country = Country('Argentina')
        other_country = Country('Brazil')
        self.assertFalse(Map({an_country, other_country}, {}).is_adjacent(an_country, other_country))

    def test_countries_are_adjacent(self):
        an_country = Country('Argentina')
        other_country = Country('Brazil')
        self.assertTrue(
            Map({an_country, other_country}, {(an_country, other_country)}).is_adjacent(an_country, other_country))

    def test_unordered_countries_are_adjancet(self):
        an_country = Country('Argentina')
        other_country = Country('Brazil')
        self.assertTrue(
            Map({an_country, other_country}, {(other_country, an_country)}).is_adjacent(an_country, other_country))
