"""Tests del submenú contextual para colocar unidades."""

# ruff: noqa: D102
# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QWidget

from pyteg.gui.mapa.menu.contextual import Menu


class ContextMenuPlaceTests(unittest.TestCase):
    """Opciones 1/3/5 y atajos del submenú Colocar unidad."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])
        cls._parent = QWidget()

    def _build_menu(self, total: int) -> Menu:
        main_window = MagicMock()
        main_window.last_units = {"Generales": total}
        main_window.misiles_habilitados = False
        main_window.scene = None
        return Menu("Argentina", "Sudamerica", main_window, parent=self._parent)

    def test_submenu_muestra_1_3_5_y_todas(self) -> None:
        menu = self._build_menu(8)
        labels = [action.text() for action in menu.submenu_colocar.actions()]
        joined = "\n".join(labels)
        self.assertIn("1", joined)
        self.assertIn("3", joined)
        self.assertIn("5", joined)
        self.assertIn("8", joined)

    def test_total_4_muestra_atajo_exacto(self) -> None:
        menu = self._build_menu(4)
        labels = [action.text() for action in menu.submenu_colocar.actions()]
        self.assertEqual(len(labels), 3)
        self.assertTrue(any("4" in label for label in labels))
