"""Prueba rápida del capturador visual usado por CI."""

# ruff: noqa: D102

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import ClassVar, cast

from PySide6.QtWidgets import QApplication

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


if __name__ == "__main__":
    unittest.main()
