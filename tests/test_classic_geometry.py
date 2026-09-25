"""Comprueba la partición única usada para dibujar el mapa clásico."""

from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET  # noqa: S405 - assets locales versionados
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path
    from typing import Any, ClassVar

MASS_NAMES = ("norteamerica", "sudamerica", "europa", "africa", "asia")
ISLANDS = {
    "Australia",
    "Borneo",
    "GranBretana",
    "Groenlandia",
    "Islandia",
    "Japon",
    "Java",
    "Madagascar",
    "Sumatra",
}
REPAIRED_BORDERS = (
    ("Canada", "NuevaYork"),
    ("Aral", "Mongolia"),
    ("China", "Iran"),
    ("China", "Mongolia"),
    ("China", "Siberia"),
    ("India", "Iran"),
    ("Iran", "Mongolia"),
)
ALPHA_THRESHOLD = 127


def _country_path(canonical: ET.Element, country: str) -> str:
    return next(
        element.attrib["d"]
        for element in canonical.iter()
        if element.get("id") == country
    )


def _pixels(image: QImage) -> Iterator[memoryview]:
    """Devuelve las filas de una máscara PNG de un byte por píxel.

    Yields:
        Una fila de etiquetas, sin bytes de relleno.

    Raises:
        AssertionError: Si Qt no cargó una máscara de escala de grises de 8 bits.

    """
    if image.format() != QImage.Format.Format_Grayscale8:
        msg = f"La máscara debe tener 8 bits por píxel: {image.format()}"
        raise AssertionError(msg)
    data = memoryview(image.constBits())
    for y in range(image.height()):
        start = y * image.bytesPerLine()
        yield data[start : start + image.width()]


def _contacts(image: QImage, names: list[str]) -> dict[frozenset[str], int]:
    """Cuenta los segmentos compartidos de la partición, sin diagonales.

    Returns:
        Cantidad de aristas de píxel para cada par de países.

    """
    contacts: dict[frozenset[str], int] = defaultdict(int)
    rows = list(_pixels(image))
    for y, row in enumerate(rows):
        next_row = rows[y + 1] if y + 1 < len(rows) else None
        for x, label in enumerate(row):
            if not label:
                continue
            for other in (
                row[x + 1] if x + 1 < len(row) else 0,
                next_row[x] if next_row is not None else 0,
            ):
                if other and other != label:
                    contacts[frozenset((names[label - 1], names[other - 1]))] += 1
    return dict(contacts)


class ClassicGeometryTests(unittest.TestCase):
    """El bloque, los países y las fronteras comparten una geometría."""

    reader: ClassVar[TomlReader]
    geometry_dir: ClassVar[Path]
    manifests: ClassVar[dict[str, dict[str, Any]]]

    @classmethod
    def setUpClass(cls) -> None:
        """Carga la configuración y los manifiestos compartidos."""
        cls.reader = TomlReader.from_theme("classic", strict=True)
        cls.geometry_dir = get_resource_path("themes/classic/geometry")
        cls.manifests = {
            mass: json.loads(
                (cls.geometry_dir / f"{mass}-manifest.json").read_text(encoding="utf-8")
            )
            for mass in MASS_NAMES
        }

    def test_partition_covers_each_block_once(self) -> None:
        """Toda tierra pertenece a exactamente un país y no queda ningún hueco."""
        all_countries: set[str] = set()
        for mass, manifest in self.manifests.items():
            with self.subTest(mass=mass):
                countries = manifest["country_order"]
                self.assertEqual(len(countries), len(set(countries)))
                self.assertFalse(all_countries.intersection(countries))
                all_countries.update(countries)

                partition = QImage(str(self.geometry_dir / f"{mass}-partition.png"))
                block = QImage(str(self.geometry_dir / f"{mass}-block.png"))
                self.assertFalse(partition.isNull())
                self.assertEqual(partition.size(), block.size())
                self.assertEqual(manifest["scale"], 4)
                self.assertEqual(
                    (partition.width(), partition.height()),
                    tuple(round(size * manifest["scale"]) for size in manifest["size"]),
                )

                counts: Counter[int] = Counter()
                for labels, land in zip(
                    _pixels(partition), _pixels(block), strict=True
                ):
                    for label, value in zip(labels, land, strict=True):
                        self.assertEqual(value, 255 if label else 0)
                        counts[label] += 1
                self.assertEqual(set(counts) - {0}, set(range(1, len(countries) + 1)))

        self.assertEqual(all_countries, set(self.reader.todos_los_paises()) - ISLANDS)
        self.assertEqual(len(all_countries), 41)

    def test_country_svgs_match_partition_and_canonical_paths(self) -> None:  # noqa: PLR0914
        """Los SVG individuales conservan cada píxel de la partición."""
        for mass, manifest in self.manifests.items():
            partition = QImage(str(self.geometry_dir / f"{mass}-partition.png"))
            labels = list(_pixels(partition))
            canonical_path = self.geometry_dir / f"{mass}-canonical.svg"
            canonical = ET.parse(canonical_path).getroot()  # noqa: S314
            self.assertTrue(QSvgRenderer(str(canonical_path)).isValid())
            self.assertTrue(
                any(
                    element.get("id", "").startswith("landmass-")
                    for element in canonical.iter()
                )
            )
            origin_x, origin_y = manifest["origin"]
            scale = manifest["scale"]
            for index, country in enumerate(manifest["country_order"], start=1):
                with self.subTest(mass=mass, country=country):
                    x, y, width, height = manifest["country_bounds"][country]
                    sprite_path = get_resource_path(
                        "themes/" + self.reader.img_path(country)
                    )
                    sprite_root = ET.parse(sprite_path).getroot()  # noqa: S314
                    sprite_d = next(
                        element.attrib["d"]
                        for element in sprite_root.iter()
                        if element.tag.endswith("path")
                    )
                    self.assertEqual(sprite_d, _country_path(canonical, country))

                    continent = self.reader.continente(country)
                    if continent is None:
                        self.fail(f"{country} no tiene continente")
                    continent_x, continent_y = self.reader.coordenadas_continente(
                        continent
                    )
                    country_x, country_y, _, _ = self.reader.coordenadas(country)
                    self.assertEqual(
                        (continent_x + country_x, continent_y + country_y), (x, y)
                    )

                    renderer = QSvgRenderer(str(sprite_path))
                    self.assertTrue(renderer.isValid())
                    self.assertEqual(renderer.viewBoxF(), QRectF(x, y, width, height))
                    image = QImage(
                        round(width * scale),
                        round(height * scale),
                        QImage.Format.Format_ARGB32,
                    )
                    image.fill(0)
                    painter = QPainter(image)
                    renderer.render(
                        painter, QRectF(0, 0, image.width(), image.height())
                    )
                    painter.end()

                    offset_x = round((x - origin_x) * scale)
                    offset_y = round((y - origin_y) * scale)
                    data = image.constBits()
                    pitch = image.bytesPerLine()
                    matching_pixels = 0
                    for row in range(image.height()):
                        expected = labels[offset_y + row]
                        for col in range(image.width()):
                            drawn = data[row * pitch + col * 4 + 3] > ALPHA_THRESHOLD
                            assigned = expected[offset_x + col] == index
                            self.assertEqual(
                                drawn,
                                assigned,
                                f"{country}: píxel {(col, row)} distinto",
                            )
                            matching_pixels += drawn
                    self.assertGreater(matching_pixels, 0)

    def test_land_borders_equal_declared_non_maritime_edges(self) -> None:
        """Las divisiones del bloque no inventan ni omiten vecinos terrestres."""
        visual = {
            frozenset((connection.origen, connection.destino))
            for connection in self.reader.get_conexiones_visuales()
        }
        for mass, manifest in self.manifests.items():
            with self.subTest(mass=mass):
                names = set(manifest["country_order"])
                expected = {
                    frozenset((origin, destination))
                    for origin in names
                    for destination in self.reader.obtener_paises_adyacentes(origin)
                    if destination in names
                    and frozenset((origin, destination)) not in visual
                }
                partition = QImage(str(self.geometry_dir / f"{mass}-partition.png"))
                contacts = _contacts(partition, manifest["country_order"])
                self.assertEqual(set(contacts), expected)
                for first, second in REPAIRED_BORDERS:
                    if first in names and second in names:
                        # Ocho píxeles de mapa a escala 4: una frontera real,
                        # no un vértice o una barra estrecha.
                        self.assertGreaterEqual(
                            contacts[frozenset((first, second))], 32
                        )

    def test_border_overlay_assets_are_valid(self) -> None:
        """El contorno y las divisiones dibujados por Qt se pueden cargar."""
        for mass in MASS_NAMES:
            with self.subTest(mass=mass):
                for suffix in ("shell", "borders"):
                    path = self.geometry_dir / f"{mass}-{suffix}.svg"
                    renderer = QSvgRenderer(str(path))
                    self.assertTrue(renderer.isValid(), str(path))
                    self.assertFalse(renderer.viewBoxF().isEmpty())


if __name__ == "__main__":
    unittest.main()
