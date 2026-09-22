"""Tests de detección de superposiciones en el layout del mapa."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage

from pyteg.gui.mapa.overlap_check import (
    BboxOverlap,
    PaisBounds,
    find_bbox_overlaps,
    find_pixel_overlaps,
    find_solid_overlaps,
    find_unconnected_boundaries,
    paises_en_punto,
)


class TestMapOverlapCheck(unittest.TestCase):
    """Intersección de bounding boxes entre países."""

    _DUMMY = Path()

    def test_sin_solapamiento(self) -> None:
        """Rectángulos separados no generan pares."""
        bounds = [
            PaisBounds("A", "C1", 0, 0, 10, 10, 0, self._DUMMY),
            PaisBounds("B", "C1", 20, 0, 10, 10, 1, self._DUMMY),
        ]
        self.assertEqual(find_bbox_overlaps(bounds), [])

    def test_solapamiento_y_orden_z(self) -> None:
        """El país con z_index mayor queda como 'encima'."""
        bounds = [
            PaisBounds("Abajo", "C1", 0, 0, 20, 20, 0, self._DUMMY),
            PaisBounds("Arriba", "C2", 10, 10, 20, 20, 1, self._DUMMY),
        ]
        overlaps = find_bbox_overlaps(bounds)
        self.assertEqual(len(overlaps), 1)
        overlap = overlaps[0]
        self.assertIsInstance(overlap, BboxOverlap)
        self.assertEqual(overlap.top.name, "Arriba")
        self.assertEqual(overlap.bottom.name, "Abajo")
        self.assertEqual(overlap.area, 100.0)

    def _sprite(self, path: Path, *, alpha: int = 255) -> None:
        image = QImage(3, 3, QImage.Format.Format_ARGB32)
        image.fill(QColor(20, 40, 60, alpha))
        self.assertTrue(image.save(str(path)))

    def test_solapamiento_solido_descarta_antialias(self) -> None:
        """El modo estricto cuenta sólo interiores sólidos."""
        with TemporaryDirectory() as directory:
            path = Path(directory)
            antialias = path / "antialias.png"
            solid = path / "solid.png"
            self._sprite(antialias, alpha=64)
            self._sprite(solid)
            bounds = [
                PaisBounds("A", "C1", 0, 0, 3, 3, 0, antialias),
                PaisBounds("B", "C1", 0, 0, 3, 3, 1, solid),
            ]

            self.assertEqual(find_pixel_overlaps(bounds)[0].opaque_pixels, 9)
            self.assertEqual(find_solid_overlaps(bounds), [])

    def test_trazo_compartido_no_cuenta_como_solapamiento_de_relleno(self) -> None:
        """Dos bordes SVG pueden coincidir sin cubrir el área del vecino."""
        with TemporaryDirectory() as directory:
            path = Path(directory)
            first_path = path / "first.svg"
            second_path = path / "second.svg"
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4" '
                'viewBox="0 0 4 4">'
                '<rect x="{x}" y="0" width="3" height="3" fill="#f7e9d9" '
                'stroke="#ffba59" stroke-width="2"/></svg>'
            )
            first_path.write_text(svg.format(x=0), encoding="utf-8")
            second_path.write_text(svg.format(x=1), encoding="utf-8")
            bounds = [
                PaisBounds("A", "C1", 0, 0, 4, 4, 0, first_path),
                PaisBounds("B", "C1", 2, 0, 4, 4, 1, second_path),
            ]

            self.assertTrue(find_pixel_overlaps(bounds))
            self.assertEqual(find_solid_overlaps(bounds), [])
            self.assertEqual(
                find_unconnected_boundaries(bounds, {"A": ["B"], "B": ["A"]}),
                [],
            )

    def test_frontera_terrestre_unida_y_separada(self) -> None:
        """Una frontera debe tocarse y una separación mayor a un píxel falla."""
        with TemporaryDirectory() as directory:
            path = Path(directory)
            first_path = path / "first.png"
            second_path = path / "second.png"
            self._sprite(first_path)
            self._sprite(second_path)
            first = PaisBounds("A", "C1", 0, 0, 3, 3, 0, first_path)
            touching = PaisBounds("B", "C1", 3, 0, 3, 3, 1, second_path)
            separated = PaisBounds("B", "C1", 5, 0, 3, 3, 1, second_path)
            adjacency = {"A": ["B"], "B": ["A"]}

            self.assertEqual(
                find_unconnected_boundaries([first, touching], adjacency), []
            )
            gaps = find_unconnected_boundaries([first, separated], adjacency)
            self.assertEqual(
                [(gap.first.name, gap.second.name) for gap in gaps],
                [("A", "B")],
            )

    def test_paises_en_punto_ignora_bounding_boxes_transparentes(self) -> None:
        """Un clic sobre transparencia no ofrece países que no están allí."""
        with TemporaryDirectory() as directory:
            path = Path(directory)
            first_path = path / "first.png"
            second_path = path / "second.png"
            first_image = QImage(3, 3, QImage.Format.Format_ARGB32)
            second_image = QImage(3, 3, QImage.Format.Format_ARGB32)
            first_image.fill(Qt.GlobalColor.transparent)
            second_image.fill(Qt.GlobalColor.transparent)
            first_image.setPixelColor(0, 0, QColor(20, 40, 60, 255))
            second_image.setPixelColor(2, 2, QColor(20, 40, 60, 255))
            self.assertTrue(first_image.save(str(first_path)))
            self.assertTrue(second_image.save(str(second_path)))
            bounds = [
                PaisBounds("A", "C1", 0, 0, 3, 3, 0, first_path),
                PaisBounds("B", "C1", 0, 0, 3, 3, 1, second_path),
            ]

            self.assertEqual(paises_en_punto(bounds, 0.5, 0.5), ["A"])
            self.assertEqual(paises_en_punto(bounds, 2.5, 2.5), ["B"])

    def test_conexion_visual_no_exige_contacto_de_siluetas(self) -> None:
        """Una ruta marítima se valida por su línea, no por tocar los sprites."""
        with TemporaryDirectory() as directory:
            path = Path(directory)
            first_path = path / "first.png"
            second_path = path / "second.png"
            self._sprite(first_path)
            self._sprite(second_path)
            bounds = [
                PaisBounds("A", "C1", 0, 0, 3, 3, 0, first_path),
                PaisBounds("B", "C2", 20, 0, 3, 3, 1, second_path),
            ]
            adjacency = {"A": ["B"], "B": ["A"]}

            self.assertEqual(
                find_unconnected_boundaries(
                    bounds,
                    adjacency,
                    visual_connections=[("A", "B")],
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
