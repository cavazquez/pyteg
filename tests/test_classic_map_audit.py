"""Regresiones del grafo oficial del mapa clásico del TEG."""

from __future__ import annotations

import unittest

from PySide6.QtGui import QImage

from pyteg.gui.mapa.overlap_check import (
    find_solid_overlaps,
    find_unconnected_boundaries,
    load_pais_bounds,
)
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

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

ISLAND_ROUTES = {
    frozenset(("GranBretana", "Alemania")),
    frozenset(("Islandia", "Suecia")),
    frozenset(("China", "Japon")),
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

    def test_gran_bretana_limita_con_espana_y_no_con_francia(self) -> None:
        """Evita confundir la frontera clásica con una conexión a Francia."""
        reader = TomlReader.from_theme("classic", strict=True)

        neighbors = set(reader.obtener_paises_adyacentes("GranBretana"))
        self.assertIn("Espana", neighbors)
        self.assertNotIn("Francia", neighbors)

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

    def test_islands_have_visual_routes_instead_of_land_borders(self) -> None:
        """Las islas mantienen su arista de juego sin pegarse al continente."""
        reader = TomlReader.from_theme("classic", strict=True)
        visual = {
            frozenset((connection.origen, connection.destino))
            for connection in reader.get_conexiones_visuales()
        }

        self.assertLessEqual(ISLAND_ROUTES, visual)

    def test_no_hay_solapamiento_solido_entre_paises(self) -> None:
        """Ningún país debe tapar píxeles sólidos de otro, sea vecino o no."""
        overlaps = find_solid_overlaps(load_pais_bounds("classic"), min_pixels=1)

        self.assertEqual(
            [
                f"{overlap.top.name}/{overlap.bottom.name}: {overlap.opaque_pixels} px"
                for overlap in overlaps
            ],
            [],
        )

    def test_land_borders_touch_without_covering_neighboring_fills(self) -> None:
        """Cada frontera terrestre queda conectada y los rellenos no se pisan."""
        reader = TomlReader.from_theme("classic", strict=True)
        bounds = load_pais_bounds("classic")
        visual_connections = [
            (connection.origen, connection.destino)
            for connection in reader.get_conexiones_visuales()
        ]

        gaps = find_unconnected_boundaries(
            bounds, reader.adyacencias, visual_connections, max_gap=1
        )

        self.assertEqual(
            [(gap.first.name, gap.second.name) for gap in gaps],
            [],
        )
        self.assertEqual(find_solid_overlaps(bounds, min_pixels=1), [])

    def test_country_sprites_have_transparent_background(self) -> None:
        """Evita rectángulos semitransparentes alrededor de los países."""
        reader = TomlReader.from_theme("classic", strict=True)

        for country in reader.todos_los_paises():
            image_path = get_resource_path("themes/" + reader.img_path(country))
            image = QImage(str(image_path))
            self.assertFalse(image.isNull(), country)

            alpha_values = {
                image.pixelColor(x, y).alpha()
                for y in range(image.height())
                for x in range(image.width())
            }
            if image_path.suffix.lower() == ".png":
                self.assertEqual(
                    alpha_values - {0, 255},
                    set(),
                    f"{country} tiene alpha intermedio: {sorted(alpha_values)}",
                )
                self.assertEqual(image.pixelColor(0, 0).alpha(), 0, country)
            else:
                # Los SVG se rasterizan con antialiasing y por eso pueden
                # contener alpha intermedio en el borde, pero nunca un fondo
                # opaco que convierta el sprite en un rectángulo.
                self.assertLess(image.pixelColor(0, 0).alpha(), 255, country)


if __name__ == "__main__":
    unittest.main()
