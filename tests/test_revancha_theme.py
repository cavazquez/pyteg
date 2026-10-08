"""Regresiones del tema estructural del mapa Revancha."""

from __future__ import annotations

import json
import tomllib
import unittest
from typing import ClassVar

from pyteg.core.cartas.mazo import Mazo
from pyteg.gui.mapa.overlap_check import (
    find_pixel_overlaps,
    find_unconnected_boundaries,
    load_pais_bounds,
    paises_en_punto,
)
from pyteg.protocol import map_hash_for_theme
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path


class RevanchaThemeTests(unittest.TestCase):
    """Comprueba que Revancha sea autocontenido y no mezcle Classic."""

    reader: ClassVar[TomlReader]

    @classmethod
    def setUpClass(cls) -> None:
        """Carga el tema estricto una sola vez."""
        cls.reader = TomlReader.from_theme("revancha", strict=True)

    def test_theme_has_72_countries_and_seven_continents(self) -> None:
        """Verifica el tamaño normativo de Revancha."""
        self.assertEqual(len(self.reader.todos_los_paises()), 72)
        self.assertEqual(len(self.reader.get_continentes()), 7)

    def test_country_deck_has_72_cards(self) -> None:
        """El mazo se construye desde los países activos del tema."""
        deck = Mazo(self.reader.todos_los_paises(), self.reader.get_simbolos())
        self.assertEqual(deck.cantidad_tarjetas(), 72)
        self.assertEqual(set(deck.dame_simbolos()), set(self.reader.get_simbolos()))

    def test_theme_has_twenty_documented_objectives(self) -> None:
        """Incluye los objetivos secretos y el objetivo común de 45 países."""
        objectives = self.reader.get_objetivos_secretos()
        self.assertEqual(len(objectives), 20)
        self.assertEqual(objectives["comun_45_paises"]["cantidad_paises"], 45)
        self.assertTrue(objectives["comun_45_paises"]["objetivo_comun"])

    def test_theme_assets_are_self_contained(self) -> None:
        """Ningún recurso del tema depende de themes/classic."""
        for path in self.reader.get_cartas().values():
            self.assertTrue(path.startswith("revancha/"), path)
            self.assertTrue(get_resource_path(f"themes/{path}").is_file(), path)

        for country in self.reader.todos_los_paises():
            path = self.reader.img_path(country)
            self.assertTrue(path.startswith("revancha/"), path)
            self.assertTrue(get_resource_path(f"themes/{path}").is_file(), path)

    def test_visual_connections_are_valid_graph_edges(self) -> None:
        """Una ruta visual nunca habilita una frontera fuera del grafo."""
        for connection in self.reader.get_conexiones_visuales():
            self.assertIn(
                connection.destino,
                self.reader.obtener_paises_adyacentes(connection.origen),
            )

    def test_country_assets_do_not_overlap(self) -> None:
        """La grilla estructural no solapa países opacos entre sí."""
        self.assertEqual(find_pixel_overlaps(load_pais_bounds("revancha")), [])

    def test_map_hash_is_different_from_classic(self) -> None:
        """El handshake distingue los dos mapas aunque compartan el protocolo."""
        self.assertNotEqual(
            map_hash_for_theme("revancha"),
            map_hash_for_theme("classic"),
        )

    def test_editable_outlines_cover_the_complete_board(self) -> None:
        """Los contornos manuales cubren los 72 IDs dentro de la referencia."""
        path = get_resource_path("themes/revancha/geometry/board-layout.toml")
        layout = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(layout["Paises"]), set(self.reader.todos_los_paises()))
        width = layout["Referencia"]["ancho"]
        height = layout["Referencia"]["alto"]
        for country in layout["Paises"].values():
            self.assertGreaterEqual(len(country["contorno"]), 3)
            for x, y in country["contorno"]:
                self.assertTrue(0 < x < width)
                self.assertTrue(0 < y < height)

    def test_army_centers_select_only_their_own_country(self) -> None:
        """Los marcadores siguen siendo sitios de clic inequívocos."""
        bounds = load_pais_bounds("revancha")
        for name in self.reader.todos_los_paises():
            with self.subTest(country=name):
                x, y, army_x, army_y = self.reader.coordenadas(name)
                self.assertEqual(
                    paises_en_punto(bounds, x + army_x + 8, y + army_y + 8),
                    [name],
                )

    def test_every_graph_edge_has_a_border_or_visible_route(self) -> None:
        """Los huecos y las islas mantienen visibles sus conexiones jugables."""
        routes = [
            (route.origen, route.destino)
            for route in self.reader.get_conexiones_visuales()
        ]
        gaps = find_unconnected_boundaries(
            load_pais_bounds("revancha"), self.reader.adyacencias, routes
        )
        self.assertEqual([(gap.first.name, gap.second.name) for gap in gaps], [])

    def test_water_background_and_geometry_source_are_declared(self) -> None:
        """La escena prolonga el mismo mar fuera del marco del tablero."""
        path = get_resource_path("themes/revancha/geometry/revancha-manifest.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source"], "board-layout.toml")
        self.assertEqual(manifest["background"], "#abc7cf")


if __name__ == "__main__":
    unittest.main()
