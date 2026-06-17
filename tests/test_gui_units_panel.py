"""Tests de helpers del panel UNIDADES."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui.managers.units_panel import format_unit_label
from tests.locale_fixtures import use_spanish


class TestFormatUnitLabel(unittest.TestCase):
    """Comprueba el formateo traducible de filas de unidades."""

    @classmethod
    def setUpClass(cls) -> None:
        use_spanish()

    def test_incluye_clave_y_valor(self) -> None:
        """El texto combina nombre de fila y cantidad."""
        texto = format_unit_label("Generales", 3)

        self.assertIn("Generales", texto)
        self.assertIn("3", texto)
        self.assertIn(":", texto)


if __name__ == "__main__":
    unittest.main()
