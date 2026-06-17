"""Tests del registro canónico de continentes en `config`."""

from __future__ import annotations

import unittest

from pyteg.config import (
    BONIFICACIONES_CONTINENTE,
    CONTINENT_PANEL_LABELS,
    CONTINENT_UNIT_SUFFIX,
    CONTINENTS,
    MAP_CONTINENT_TO_PANEL_LABEL,
)


class TestContinentsConfig(unittest.TestCase):
    """Derivados coherentes con TOML y panel GUI."""

    def test_map_ids_unicos(self) -> None:
        """Cada continente tiene un `map_id` distinto."""
        ids = [spec.map_id for spec in CONTINENTS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_bonificaciones_definidas_en_registro(self) -> None:
        """Cada continente del registro tiene bonificación derivada."""
        for spec in CONTINENTS:
            self.assertEqual(BONIFICACIONES_CONTINENTE[spec.map_id], spec.bonus)

    def test_derivados_cubren_todos_los_continentes(self) -> None:
        """Panel, sufijos y bonificaciones derivan del mismo registro."""
        for spec in CONTINENTS:
            self.assertIn(spec.panel_label, CONTINENT_PANEL_LABELS)
            self.assertEqual(
                MAP_CONTINENT_TO_PANEL_LABEL[spec.map_id], spec.panel_label
            )
            self.assertEqual(CONTINENT_UNIT_SUFFIX[spec.map_id], spec.unit_suffix)
            self.assertEqual(BONIFICACIONES_CONTINENTE[spec.map_id], spec.bonus)


if __name__ == "__main__":
    unittest.main()
