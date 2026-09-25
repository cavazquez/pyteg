"""Regresión de assets SVG del mapa clásico."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar, cast

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from pyteg.gui.mapa.pais import Pais
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication as QApplicationType


class MapSvgAssetsTests(unittest.TestCase):
    """Comprueba carga y render de assets sin abrir una ventana."""

    app: ClassVar[QApplicationType]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplicationType", QApplication.instance() or QApplication([]))

    def _scene(self) -> QCustomGraphicsScene:
        main_window = SimpleNamespace(
            scene=None,
            update_status_bar=lambda *_args: None,
            clear_status_bar=lambda: None,
        )
        scene = QCustomGraphicsScene(main_window, theme="classic")
        main_window.scene = scene
        return scene

    def test_assets_criticos_se_cargan_como_svg(self) -> None:
        scene = self._scene()
        self.assertEqual(len(scene.paises), 50)
        for name, size in {
            "Chile": (21, 81),
            "Groenlandia": (83, 89),
            "Australia": (67, 52),
        }.items():
            pais = scene.paises[name]
            self.assertTrue(pais.es_vectorial)
            self.assertEqual((pais.pixmap().width(), pais.pixmap().height()), size)
            self.assertTrue(pais.ruta_asset.endswith(".svg"))

    def test_todos_los_paises_clasicos_tienen_svg_y_fallback_png(self) -> None:
        reader = TomlReader.from_theme("classic", strict=True)
        countries = reader.todos_los_paises()
        self.assertEqual(len(countries), 50)
        for country in countries:
            asset = Path(get_resource_path("themes/" + reader.img_path(country)))
            self.assertEqual(asset.suffix, ".svg", country)
            self.assertTrue(asset.with_suffix(".png").is_file(), country)

    def test_render_vectorial_no_queda_vacio_en_zoom(self) -> None:
        scene = self._scene()
        image = QImage(1280, 800, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        scene.render(painter, QRectF(0, 0, 1280, 800), scene.sceneRect())
        painter.end()
        self.assertGreater(image.sizeInBytes(), 0)
        self.assertTrue(any(image.pixelColor(x, 400).alpha() > 0 for x in range(1280)))

    def test_svg_invalido_usa_png_de_respaldo(self) -> None:
        with TemporaryDirectory() as temp_dir:
            svg_path = Path(temp_dir) / "pais.svg"
            png_path = svg_path.with_suffix(".png")
            svg_path.write_text("<svg roto", encoding="utf-8")
            image = QImage(8, 8, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(0)
            self.assertTrue(
                image.save(str(png_path), "PNG")  # type: ignore[call-overload]
            )

            pais = Pais(str(svg_path), ("Respaldo", "Test"), (0, 0, 1, 1))

            self.assertFalse(pais.es_vectorial)
            self.assertTrue(pais.ruta_asset.endswith(".png"))


if __name__ == "__main__":
    unittest.main()
