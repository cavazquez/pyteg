"""Validación del inventario y del grafo auditado del mapa Revancha."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path
from typing import Any, ClassVar

from pyteg.toml_reader import TomlReader

FIXTURE = Path(__file__).parent / "fixtures" / "revancha_map_audit.toml"
EXPECTED_COUNTS = {
    "AmericaDelNorte": 12,
    "AmericaCentral": 6,
    "AmericaDelSur": 8,
    "Europa": 16,
    "Africa": 8,
    "Asia": 16,
    "Oceania": 6,
}
EXPECTED_COUNTRIES = {
    "AmericaDelNorte": {
        "Alaska",
        "California",
        "Canada",
        "Chicago",
        "Florida",
        "Groenlandia",
        "IslaVictoria",
        "LasVegas",
        "Labrador",
        "NuevaYork",
        "Oregon",
        "Terranova",
    },
    "AmericaCentral": {
        "Cuba",
        "ElSalvador",
        "Honduras",
        "Jamaica",
        "Mexico",
        "Nicaragua",
    },
    "AmericaDelSur": {
        "Argentina",
        "Bolivia",
        "Brasil",
        "Chile",
        "Colombia",
        "Paraguay",
        "Uruguay",
        "Venezuela",
    },
    "Europa": {
        "Albania",
        "Alemania",
        "Bielorrusia",
        "Croacia",
        "Espana",
        "Finlandia",
        "Francia",
        "GranBretana",
        "Irlanda",
        "Islandia",
        "Italia",
        "Noruega",
        "Polonia",
        "Portugal",
        "Serbia",
        "Ucrania",
    },
    "Africa": {
        "Angola",
        "Egipto",
        "Etiopia",
        "Madagascar",
        "Mauritania",
        "Nigeria",
        "Sahara",
        "Sudafrica",
    },
    "Asia": {
        "Arabia",
        "Chechenia",
        "China",
        "Chukchi",
        "Corea",
        "India",
        "Iran",
        "Irak",
        "Israel",
        "Japon",
        "Kamchatka",
        "Malasia",
        "Rusia",
        "Siberia",
        "Turquia",
        "Vietnam",
    },
    "Oceania": {
        "Australia",
        "Filipinas",
        "NuevaZelandia",
        "Sumatra",
        "Tasmania",
        "Tonga",
    },
}


class RevanchaMapAuditTests(unittest.TestCase):
    """Evita que el tema Revancha pierda países o fronteras auditadas."""

    audit: ClassVar[dict[str, Any]]
    continents: ClassVar[dict[str, Any]]
    countries: ClassVar[set[str]]
    adjacency: ClassVar[dict[str, list[str]]]
    reader: ClassVar[TomlReader]

    @classmethod
    def setUpClass(cls) -> None:
        """Carga el fixture una sola vez para la batería de invariantes."""
        cls.audit = tomllib.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.continents = cls.audit["Continentes"]
        cls.countries = {
            country
            for continent in cls.continents.values()
            for country in continent["paises"]
        }
        cls.adjacency = cls.audit["Adyacencias"]
        cls.reader = TomlReader.from_theme("revancha", strict=True)

    def test_fixture_has_seven_continents_and_72_countries(self) -> None:
        """Verifica el inventario completo y sus siete cantidades."""
        self.assertEqual(self.audit["Meta"]["total_continentes"], 7)
        self.assertEqual(self.audit["Meta"]["total_paises"], 72)
        self.assertEqual(set(self.continents), set(EXPECTED_COUNTS))
        self.assertEqual(len(self.countries), 72)
        self.assertEqual(
            {key: value["cantidad"] for key, value in self.continents.items()},
            EXPECTED_COUNTS,
        )
        self.assertEqual(
            {key: set(value["paises"]) for key, value in self.continents.items()},
            EXPECTED_COUNTRIES,
        )

    def test_every_country_belongs_to_one_continent(self) -> None:
        """Evita duplicar o dejar un país fuera de un continente."""
        memberships = [
            country
            for continent in self.continents.values()
            for country in continent["paises"]
        ]
        self.assertEqual(len(memberships), len(set(memberships)))

    def test_audited_graph_is_complete_and_symmetric(self) -> None:
        """Verifica que las 134 aristas sean válidas y bidireccionales."""
        self.assertEqual(set(self.adjacency), self.countries)
        self.assertEqual(self.audit["Meta"]["aristas_no_dirigidas"], 134)

        for country, neighbors in self.adjacency.items():
            self.assertNotIn(country, neighbors)
            self.assertEqual(len(neighbors), len(set(neighbors)), country)
            self.assertTrue(set(neighbors) <= self.countries, country)
            for neighbor in neighbors:
                self.assertIn(country, self.adjacency[neighbor])

        edges = {
            frozenset((country, neighbor))
            for country, neighbors in self.adjacency.items()
            for neighbor in neighbors
        }
        self.assertEqual(len(edges), 134)

    def test_audited_graph_is_connected(self) -> None:
        """Los 72 países pueden alcanzarse mediante conexiones jugables."""
        visited: set[str] = set()
        pending = [next(iter(self.countries))]
        while pending:
            country = pending.pop()
            if country not in visited:
                visited.add(country)
                pending.extend(self.adjacency[country])
        self.assertEqual(visited, self.countries)

    def test_theme_inventory_matches_audit(self) -> None:
        """Detecta países agregados, eliminados o movidos de continente."""
        self.assertEqual(set(self.reader.todos_los_paises()), self.countries)
        actual = {
            continent: set(self.reader.get_paises(continent))
            for continent in self.reader.get_continentes()
        }
        expected = {
            continent: set(data["paises"])
            for continent, data in self.continents.items()
        }
        self.assertEqual(actual, expected)

    def test_theme_adjacency_matches_audit(self) -> None:
        """Detecta cualquier frontera cambiada sin actualizar el fixture."""
        for country in self.reader.todos_los_paises():
            neighbors = self.reader.obtener_paises_adyacentes(country)
            self.assertEqual(len(neighbors), len(set(neighbors)), country)
        actual = {
            country: set(self.reader.obtener_paises_adyacentes(country))
            for country in self.reader.todos_los_paises()
        }
        expected = {
            country: set(neighbors) for country, neighbors in self.adjacency.items()
        }
        self.assertEqual(actual, expected)

    def test_intercontinental_edges_match_documented_list(self) -> None:
        """Comprueba las 20 conexiones entre continentes, terrestres o de agua."""
        memberships = {
            country: continent
            for continent, data in self.continents.items()
            for country in data["paises"]
        }
        actual = {
            frozenset((origin, destination))
            for origin, neighbors in self.adjacency.items()
            for destination in neighbors
            if memberships[origin] != memberships[destination]
        }
        pairs = self.audit["FronterasIntercontinentales"]["pares"]
        expected = {frozenset(pair) for pair in pairs}
        self.assertEqual(len(pairs), len(expected))
        self.assertEqual(len(expected), 20)
        self.assertEqual(actual, expected)

    def test_documented_bridges_are_present(self) -> None:
        """Verifica los puentes largos y sus rutas visuales permanentes."""
        bridges = {frozenset(pair) for pair in self.audit["Puentes"]["consenso"]}
        routes = {
            frozenset((route.origen, route.destino))
            for route in self.reader.get_conexiones_visuales()
        }
        for origin, destination in bridges:
            self.assertIn(destination, self.adjacency[origin])
            self.assertIn(frozenset((origin, destination)), routes)

        # Ejemplos de puentes explícitos en las reglas configuradas.
        for pair in (("Alaska", "Chukchi"), ("Chile", "Australia")):
            self.assertIn(pair[1], self.adjacency[pair[0]])

    def test_source_discrepancies_have_explicit_resolutions(self) -> None:
        """Cada exclusión queda registrada con su motivo y procedencia."""
        self.assertEqual(self.audit["Meta"]["schema_version"], 2)
        self.assertEqual(self.audit["Meta"]["estado_grafo"], "auditado_para_pyteg")
        self.assertEqual(self.audit["Meta"]["aristas_pendientes"], [])
        self.assertEqual(self.audit["Discrepancias"]["pendientes"], [])
        decisions = self.audit["Discrepancias"]["resueltas"]
        excluded = {
            frozenset(("GranBretana", "Francia")),
            frozenset(("Irak", "Ucrania")),
            frozenset(("Uruguay", "Mauritania")),
        }
        self.assertEqual(len(decisions), len(excluded))
        self.assertEqual({frozenset(item["arista"]) for item in decisions}, excluded)
        for decision in decisions:
            self.assertFalse(decision["incluida"])
            self.assertTrue(decision["motivo"].strip())
            self.assertTrue(decision["fuentes"])
            self.assertTrue(set(decision["fuentes"]) <= set(self.audit["Fuentes"]))
            origin, destination = decision["arista"]
            self.assertNotIn(destination, self.adjacency[origin])
            self.assertNotIn(origin, self.adjacency[destination])

    def test_resolved_connections_remain_present(self) -> None:
        """Conserva los extremos aceptados de las conexiones discutidas."""
        for origin, destination in (
            ("GranBretana", "Portugal"),
            ("Iran", "Ucrania"),
            ("Uruguay", "Nigeria"),
        ):
            with self.subTest(origin=origin, destination=destination):
                self.assertIn(destination, self.adjacency[origin])
                self.assertIn(origin, self.adjacency[destination])
        self.assertEqual(
            set(self.adjacency["GranBretana"]), {"Alemania", "Irlanda", "Portugal"}
        )
        self.assertEqual(
            set(self.adjacency["Ucrania"]),
            {"Albania", "Bielorrusia", "Iran", "Polonia", "Rusia"},
        )


if __name__ == "__main__":
    unittest.main()
