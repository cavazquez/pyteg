"""Validación del inventario y del grafo auditado de TEG La Revancha."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path
from typing import Any, ClassVar

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
    """Evita que el futuro tema Revancha pierda países o fronteras."""

    audit: ClassVar[dict[str, Any]]
    continents: ClassVar[dict[str, Any]]
    countries: ClassVar[set[str]]
    adjacency: ClassVar[dict[str, list[str]]]

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

    def test_consensus_graph_is_complete_and_symmetric(self) -> None:
        """Verifica que las 134 aristas sean válidas y bidireccionales."""
        self.assertEqual(set(self.adjacency), self.countries)
        self.assertEqual(self.audit["Meta"]["aristas_no_dirigidas"], 134)

        for country, neighbors in self.adjacency.items():
            self.assertNotIn(country, neighbors)
            self.assertTrue(set(neighbors) <= self.countries, country)
            for neighbor in neighbors:
                self.assertIn(country, self.adjacency[neighbor])

        edges = {
            frozenset((country, neighbor))
            for country, neighbors in self.adjacency.items()
            for neighbor in neighbors
        }
        self.assertEqual(len(edges), 134)

    def test_documented_bridges_are_present(self) -> None:
        """Verifica los puentes intercontinentales documentados."""
        bridges = {frozenset(pair) for pair in self.audit["Puentes"]["consenso"]}
        for origin, destination in bridges:
            self.assertIn(destination, self.adjacency[origin])

        # Ejemplos de puentes explícitos en el reglamento oficial.
        for pair in (("Alaska", "Chukchi"), ("Chile", "Australia")):
            self.assertIn(pair[1], self.adjacency[pair[0]])

    def test_disputed_edge_remains_explicitly_pending(self) -> None:
        """Evita activar una frontera cuya fuente todavía discrepa."""
        pending = {"GranBretana-Francia", "Irak-Ucrania"}
        self.assertEqual(set(self.audit["Meta"]["aristas_pendientes"]), pending)
        self.assertEqual(set(self.audit["Discrepancias"]["pendientes"]), pending)
        self.assertNotIn("Francia", self.adjacency["GranBretana"])
        self.assertNotIn("Ucrania", self.adjacency["Irak"])


if __name__ == "__main__":
    unittest.main()
