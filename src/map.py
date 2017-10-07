class Map():
    def __init__(self, countries, adjacent):
        self._countries = countries
        self._adjacent = dict(set())

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
