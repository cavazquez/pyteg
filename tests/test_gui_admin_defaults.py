"""Regresiones de los valores predeterminados de la ventana de administración."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast

from PySide6.QtWidgets import QApplication

from pyteg.config import DEFAULT_VICTORY_COUNTRIES
from pyteg.gui.windows.admin import VentanaAdmin


class AdminDefaultsTests(unittest.TestCase):
    """La UI debe comenzar con el mismo objetivo que ``GameConfig``."""

    _app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        existing_app = QApplication.instance()
        cls._app = (
            cast("QApplication", existing_app)
            if existing_app is not None
            else QApplication([])
        )

    def test_objetivo_predeterminado_es_30_paises(self) -> None:
        ventana = VentanaAdmin(SimpleNamespace())

        self.assertTrue(ventana.countries_checkbox.isChecked())
        self.assertEqual(ventana.countries_input.text(), str(DEFAULT_VICTORY_COUNTRIES))


if __name__ == "__main__":
    unittest.main()
