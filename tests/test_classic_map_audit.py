"""Regresiones del grafo oficial del mapa clásico del TEG."""

from __future__ import annotations

import unittest

from pyteg.toml_reader import TomlReader

EXPECTED_CONTINENTS: dict[str, set[str]] = {
    "Sudamerica": {"Argentina", "Brasil", "Chile", "Colombia", "Peru", "Uruguay"},
    "Norteamerica": {
        "Alaska",
        "California",
        "Canada",
        "Groenlandia",
        "Labrador",
        "Mexico",
        "NuevaYork",
        "Oregon",
        "Terranova",
        "Yukon",
    },
    "Europa": {
        "Alemania",
        "Espana",
        "Francia",
        "GranBretana",
        "Islandia",
        "Italia",
        "Polonia",
        "Rusia",
        "Suecia",
    },
    "Africa": {"Egipto", "Etiopia", "Madagascar", "Sahara", "Sudafrica", "Zaire"},
    "Asia": {
        "Arabia",
        "Aral",
        "China",
        "Gobi",
        "India",
        "Iran",
        "Israel",
        "Japon",
        "Kamchatka",
        "Malasia",
        "Mongolia",
        "Siberia",
        "Taimiria",
        "Tartaria",
        "Turquia",
    },
    "Oceania": {"Australia", "Borneo", "Java", "Sumatra"},
}

EXPECTED_ADJACENCY: dict[str, set[str]] = {
    "Argentina": {"Brasil", "Chile", "Peru", "Uruguay"},
    "Brasil": {"Argentina", "Colombia", "Peru", "Sahara", "Uruguay"},
    "Chile": {"Argentina", "Australia", "Peru"},
    "Colombia": {"Brasil", "Mexico", "Peru"},
    "Peru": {"Argentina", "Brasil", "Chile", "Colombia"},
    "Uruguay": {"Argentina", "Brasil"},
    "Alaska": {"Kamchatka", "Oregon", "Yukon"},
    "California": {"Mexico", "NuevaYork", "Oregon"},
    "Canada": {"NuevaYork", "Oregon", "Terranova", "Yukon"},
    "Groenlandia": {"Islandia", "Labrador", "NuevaYork"},
    "Labrador": {"Groenlandia", "Terranova"},
    "Mexico": {"California", "Colombia"},
    "NuevaYork": {"California", "Canada", "Groenlandia", "Oregon", "Terranova"},
    "Oregon": {"Alaska", "California", "Canada", "NuevaYork", "Yukon"},
    "Terranova": {"Canada", "Labrador", "NuevaYork"},
    "Yukon": {"Alaska", "Canada", "Oregon"},
    "Alemania": {"Francia", "GranBretana", "Italia", "Polonia"},
    "Espana": {"Francia", "GranBretana", "Sahara"},
    "Francia": {"Alemania", "Espana", "Italia"},
    "GranBretana": {"Alemania", "Espana", "Islandia"},
    "Islandia": {"GranBretana", "Groenlandia", "Suecia"},
    "Italia": {"Alemania", "Francia"},
    "Polonia": {"Alemania", "Egipto", "Rusia", "Turquia"},
    "Rusia": {"Aral", "Iran", "Polonia", "Suecia", "Turquia"},
    "Suecia": {"Islandia", "Rusia"},
    "Egipto": {"Etiopia", "Israel", "Madagascar", "Polonia", "Sahara", "Turquia"},
    "Etiopia": {"Egipto", "Sahara", "Sudafrica", "Zaire"},
    "Madagascar": {"Egipto", "Zaire"},
    "Sahara": {"Brasil", "Egipto", "Espana", "Etiopia", "Zaire"},
    "Sudafrica": {"Etiopia", "Zaire"},
    "Zaire": {"Etiopia", "Madagascar", "Sahara", "Sudafrica"},
    "Arabia": {"Israel", "Turquia"},
    "Aral": {"Iran", "Mongolia", "Rusia", "Siberia", "Tartaria"},
    "China": {
        "Gobi",
        "India",
        "Iran",
        "Japon",
        "Kamchatka",
        "Malasia",
        "Mongolia",
        "Siberia",
    },
    "Gobi": {"China", "Iran", "Mongolia"},
    "India": {"China", "Iran", "Malasia", "Sumatra"},
    "Iran": {"Aral", "China", "Gobi", "India", "Mongolia", "Rusia", "Turquia"},
    "Israel": {"Arabia", "Egipto", "Turquia"},
    "Japon": {"China", "Kamchatka"},
    "Kamchatka": {"Alaska", "China", "Japon", "Siberia"},
    "Malasia": {"Borneo", "China", "India"},
    "Mongolia": {"Aral", "China", "Gobi", "Iran", "Siberia"},
    "Siberia": {"Aral", "China", "Kamchatka", "Mongolia", "Taimiria", "Tartaria"},
    "Taimiria": {"Siberia", "Tartaria"},
    "Tartaria": {"Aral", "Siberia", "Taimiria"},
    "Turquia": {"Arabia", "Egipto", "Iran", "Israel", "Polonia", "Rusia"},
    "Australia": {"Borneo", "Chile", "Java", "Sumatra"},
    "Borneo": {"Australia", "Malasia"},
    "Java": {"Australia"},
    "Sumatra": {"Australia", "India"},
}

EXPECTED_BRIDGES = {
    frozenset(pair)
    for pair in (
        ("Alaska", "Kamchatka"),
        ("Brasil", "Sahara"),
        ("Chile", "Australia"),
        ("Colombia", "Mexico"),
        ("Egipto", "Israel"),
        ("Egipto", "Polonia"),
        ("Egipto", "Turquia"),
        ("Espana", "Sahara"),
        ("Groenlandia", "Islandia"),
        ("India", "Sumatra"),
        ("Malasia", "Borneo"),
        ("Polonia", "Turquia"),
        ("Rusia", "Aral"),
        ("Rusia", "Iran"),
        ("Rusia", "Turquia"),
    )
}


def _edges(adjacency: dict[str, list[str]]) -> set[frozenset[str]]:
    return {
        frozenset((origin, destination))
        for origin, destinations in adjacency.items()
        for destination in destinations
        if origin != destination
    }


class ClassicMapAuditTests(unittest.TestCase):
    """Verifica que el tema clásico conserve la topología auditada."""

    def test_continents_and_countries_match_classic_board(self) -> None:
        """Verifica la lista de países y su continente."""
        reader = TomlReader.from_theme("classic", strict=True)

        self.assertEqual(set(reader.get_continentes()), set(EXPECTED_CONTINENTS))
        self.assertEqual(len(reader.todos_los_paises()), 50)
        for continent, expected_countries in EXPECTED_CONTINENTS.items():
            self.assertEqual(set(reader.get_paises(continent)), expected_countries)

    def test_adjacency_graph_matches_classic_board(self) -> None:
        """Verifica todas las aristas y la simetría del grafo."""
        reader = TomlReader.from_theme("classic", strict=True)

        actual = {
            country: set(reader.obtener_paises_adyacentes(country))
            for country in reader.todos_los_paises()
        }
        self.assertEqual(actual, EXPECTED_ADJACENCY)
        self.assertEqual(
            _edges(reader.adyacencias),
            _edges({
                country: sorted(neighbors)
                for country, neighbors in EXPECTED_ADJACENCY.items()
            }),
        )

    def test_intercontinental_bridges_match_classic_board(self) -> None:
        """Verifica los quince puentes entre continentes."""
        reader = TomlReader.from_theme("classic", strict=True)
        country_to_continent = {
            country: continent
            for continent in reader.get_continentes()
            for country in reader.get_paises(continent)
        }
        actual_bridges = {
            frozenset((origin, destination))
            for origin, destinations in reader.adyacencias.items()
            for destination in destinations
            if country_to_continent[origin] != country_to_continent[destination]
        }

        self.assertEqual(actual_bridges, EXPECTED_BRIDGES)

    def test_visual_connections_are_valid_edges(self) -> None:
        """Verifica que una línea visual no habilite una arista falsa."""
        reader = TomlReader.from_theme("classic", strict=True)

        for connection in reader.get_conexiones_visuales():
            self.assertIn(
                connection.destino,
                reader.obtener_paises_adyacentes(connection.origen),
            )


if __name__ == "__main__":
    unittest.main()
