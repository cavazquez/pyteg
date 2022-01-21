from src.country import Country
from typing import Dict, Set

class Map:
    def __init__(self, countries: set[Country], adjacent: list[tuple]):
        self._countries = countries
        self._adjacent: Dict[str, Set[str]] = dict(set())

        for elems in adjacent:
            try:
                self._adjacent[elems[0]].add(elems[1])
            except KeyError:
                self._adjacent[elems[0]] = {elems[1]}

    def get_countries(self):
        return self._countries

    def is_adjacent(self, an_country, other_country):
        try:
            return other_country in self._adjacent[an_country]
        except KeyError:
            return False
