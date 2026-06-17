"""Tests para disponibilidad de unidades al colocar refuerzos (GUI)."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui.units_placement import (
    tooltip_colocar_unidad,
    unidades_colocables_en_pais,
)
from tests.locale_fixtures import use_spanish


class TestUnitsPlacement(unittest.TestCase):
    """Suma continental + generales como en el servidor."""

    @classmethod
    def setUpClass(cls) -> None:
        use_spanish()

    def test_suma_bonificacion_y_generales(self) -> None:
        """Suma bonificación continental y unidades generales."""
        last_units = {"Generales": 4, "África": 2}
        total, cont, gen = unidades_colocables_en_pais(last_units, "Africa")
        self.assertEqual((total, cont, gen), (6, 2, 4))

    def test_solo_generales_si_no_hay_bonificacion(self) -> None:
        """Sin bonificación continental solo cuenta generales."""
        last_units = {"Generales": 3, "África": 0}
        total, cont, gen = unidades_colocables_en_pais(last_units, "Africa")
        self.assertEqual((total, cont, gen), (3, 0, 3))

    def test_tooltip_sin_unidades(self) -> None:
        """Tooltip indica ausencia de unidades."""
        tooltip = tooltip_colocar_unidad({"Generales": 0}, "Sudamerica")
        self.assertIn("Sin unidades", tooltip)

    def test_tooltip_con_continental_y_generales(self) -> None:
        """Tooltip menciona continente y generales cuando ambos hay stock."""
        last_units = {"Generales": 2, "América del Sur": 1}
        tooltip = tooltip_colocar_unidad(last_units, "Sudamerica")
        self.assertIn("América del Sur", tooltip)
        self.assertIn("2", tooltip)


if __name__ == "__main__":
    unittest.main()
