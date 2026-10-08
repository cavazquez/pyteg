"""Prueba rápida del capturador visual usado por CI."""

# ruff: noqa: D102

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import ClassVar, cast

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from scripts.color_vision import simulate_color, simulate_image
from scripts.smoke_visual_map import render_capture


class VisualMapSmokeTests(unittest.TestCase):
    """El render offscreen produce una imagen revisable y metadatos válidos."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def test_captura_classic_pequena(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            record = render_capture(self.app, "classic", (1024, 600), output_dir)
            self.assertEqual(record.countries, 50)
            self.assertGreater(record.visual_connections, 0)
            self.assertTrue(Path(record.output).is_file())

    def test_captura_revancha_pequena(self) -> None:
        """El tema Revancha renderiza sus 72 países con rutas propias."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            record = render_capture(self.app, "revancha", (1024, 600), output_dir)
            self.assertEqual(record.countries, 72)
            self.assertGreater(record.visual_connections, 0)
            self.assertTrue(Path(record.output).is_file())

    def test_captura_revancha_con_zoom_y_simulacion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            record = render_capture(
                self.app,
                "revancha",
                (1024, 600),
                Path(temp_dir),
                zoom=1.5,
                color_vision="deuteranopia",
            )
            self.assertEqual(record.countries, 72)
            self.assertEqual(record.zoom, 1.5)
            self.assertEqual(record.color_vision, "deuteranopia")
            self.assertIn("zoom-1.5-deuteranopia", record.output)
            self.assertFalse(QImage(record.output).isNull())

    def test_simulacion_conserva_alpha_y_no_modifica_original(self) -> None:
        image = QImage(1, 1, QImage.Format.Format_RGBA8888)
        original = QColor(255, 0, 0, 128)
        image.fill(original)
        simulated = simulate_image(image, "deuteranopia")
        self.assertEqual(image.pixelColor(0, 0), original)
        self.assertEqual(
            simulated.pixelColor(0, 0), simulate_color(original, "deuteranopia")
        )

    def test_rechaza_zoom_invalido(self) -> None:
        for zoom in (0, -1, float("inf"), float("nan")):
            with self.subTest(zoom=zoom), self.assertRaises(ValueError):
                render_capture(
                    self.app, "revancha", (1024, 600), Path("unused"), zoom=zoom
                )


if __name__ == "__main__":
    unittest.main()
