"""Regresiones de legibilidad del mapa y de las fichas de unidades."""

# ruff: noqa: D102

from __future__ import annotations

import json
import unittest
from itertools import combinations, starmap
from types import SimpleNamespace
from typing import ClassVar, cast
from unittest.mock import patch

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPolygonF
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from pyteg.gui.color_contrast import contrast_ratio
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.gui.widgets.circulo import Circulo
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path
from scripts.color_vision import COLOR_VISION_MODES, simulate_color, simulate_rgb
from tests.qt_fixtures import dispose_object


class RevanchaVisualLayoutTests(unittest.TestCase):
    """Comprueba el layout generado contra la geometría real que carga Qt."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        self.scene = QCustomGraphicsScene(SimpleNamespace(), theme="revancha")
        self.addCleanup(dispose_object, self.scene)
        self.manifest = json.loads(
            get_resource_path(
                "themes/revancha/geometry/revancha-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.labels = {}
        for name, label in self.manifest["labels"].items():
            path = QPainterPath()
            path.addPolygon(
                QPolygonF(list(starmap(QPointF, label["reserved_polygon"])))
            )
            path.closeSubpath()
            self.labels[name] = path

    def test_all_country_labels_exist_and_fit_on_board(self) -> None:
        self.assertEqual(set(self.labels), set(self.scene.paises))
        renderer = QSvgRenderer(
            str(get_resource_path("themes/revancha/geometry/revancha-borders.svg"))
        )
        self.assertTrue(renderer.isValid())
        board = QRectF(0, 0, *self.manifest["size"])
        for name, path in self.labels.items():
            with self.subTest(country=name):
                element = f"country-label-{name}"
                self.assertTrue(renderer.elementExists(element))
                self.assertTrue(board.contains(path.boundingRect()))
                self.assertTrue(
                    path.boundingRect().contains(renderer.boundsOnElement(element))
                )

    def test_country_labels_do_not_overlap(self) -> None:
        for (first, first_path), (second, second_path) in combinations(
            self.labels.items(), 2
        ):
            with self.subTest(first=first, second=second):
                self.assertFalse(first_path.intersects(second_path))

    def test_entire_marker_including_border_is_inside_country(self) -> None:
        for name, country in self.scene.paises.items():
            with self.subTest(country=name):
                circle = country._circle  # noqa: SLF001
                self.assertIsNotNone(circle)
                if circle is None:
                    self.fail("No se cargó la ficha del país")
                marker = circle.mapToScene(circle.shape())
                self.assertTrue(country.mapToScene(country.shape()).contains(marker))
                for label_name, label in self.labels.items():
                    self.assertFalse(marker.intersects(label), (name, label_name))

    def test_routes_and_labels_do_not_intercept_country_clicks(self) -> None:
        for route in self.scene.visual_connections:
            self.assertEqual(route.acceptedMouseButtons(), Qt.MouseButton.NoButton)
            self.assertLess(route.zValue(), 0)
            self.assertGreater(route.zValue(), -500)
            self.assertTrue(route.pen().isCosmetic())
            for arrow in route.childItems():
                self.assertEqual(arrow.acceptedMouseButtons(), Qt.MouseButton.NoButton)
        for layer in self.scene.landmass_borders:
            self.assertEqual(layer.acceptedMouseButtons(), Qt.MouseButton.NoButton)
        reader = TomlReader.from_theme("revancha", strict=True)
        with patch.object(self.scene.selection_manager, "seleccionar_pais") as selected:
            for name in reader.todos_los_paises():
                x, y, ax, ay = reader.coordenadas(name)
                self.assertTrue(
                    self.scene.handle_country_click(QPointF(x + ax + 8, y + ay + 8))
                )
                selected.assert_called_with(name)

    def test_routes_and_names_keep_contrast_under_color_simulation(self) -> None:
        sea = ("#d9e4df", "#c8dcdc", "#abc7cf", "#f0ead4")
        for mode in COLOR_VISION_MODES:
            with self.subTest(simulation=mode):
                for route in self.scene.visual_connections:
                    foreground = simulate_color(route.pen().color(), mode)
                    for background in sea:
                        self.assertGreaterEqual(
                            contrast_ratio(
                                foreground, simulate_color(QColor(background), mode)
                            ),
                            3,
                        )
                self.assertGreaterEqual(
                    contrast_ratio(
                        simulate_color(QColor(self.manifest["label_ink"]), mode),
                        simulate_color(QColor(self.manifest["label_halo"]), mode),
                    ),
                    4.5,
                )


class ArmyTextLayoutTests(unittest.TestCase):
    """La ficha conserva la cantidad y ajusta su texto al círculo en ambos mapas."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def test_text_recenters_and_fits_when_quantity_changes(self) -> None:
        circle = Circulo(17, 29)
        text = circle._center_text  # noqa: SLF001
        for quantity in (0, 1, 12, 123, 1234, 1):
            with self.subTest(quantity=quantity):
                circle.set_unidades(quantity)
                self.assertEqual(circle.get_unidades(), quantity)
                bounds = text.mapRectToParent(text.boundingRect())
                self.assertTrue(circle.rect().contains(bounds))
                self.assertAlmostEqual(bounds.center().x(), circle.rect().center().x())
                self.assertAlmostEqual(bounds.center().y(), circle.rect().center().y())
                self.assertEqual(text.acceptedMouseButtons(), Qt.MouseButton.NoButton)

    def test_number_ink_has_contrast_with_player_color(self) -> None:
        circle = Circulo(0, 0)
        for fill in ("#d32f2f", "#1976d2", "#fbc02d", "#388e3c", "#00ff00", "#7b7b7b"):
            with self.subTest(color=fill):
                circle.set_color(fill)
                ink = circle._center_text.defaultTextColor()  # noqa: SLF001
                self.assertGreaterEqual(contrast_ratio(ink, QColor(fill)), 4.5)

    def test_color_simulation_uses_linear_rgb_and_clamps_gamut(self) -> None:
        self.assertEqual(simulate_rgb(255, 0, 0, "deuteranopia"), (163, 144, 0))
        for mode in COLOR_VISION_MODES:
            self.assertEqual(simulate_rgb(255, 255, 255, mode), (255, 255, 255))
            self.assertEqual(simulate_rgb(0, 0, 0, mode), (0, 0, 0))
        self.assertAlmostEqual(contrast_ratio(QColor("black"), QColor("white")), 21)
        with self.assertRaises(ValueError):
            simulate_rgb(0, 0, 0, "unknown")
