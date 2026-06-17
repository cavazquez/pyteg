"""Tests de posición del marcador de unidades."""

from __future__ import annotations

import unittest

from pyteg.gui.mapa.army_position import resolve_army_position


class TestArmyPosition(unittest.TestCase):
    """Centrado por defecto y clamp dentro del sprite."""

    def test_cero_cero_usa_centro(self) -> None:
        """Sin coordenadas en TOML, el círculo va al centro."""
        x, y = resolve_army_position(80, 100, 0, 0)
        self.assertEqual((x, y), (32.0, 42.0))

    def test_coordenadas_negativas_se_clampean(self) -> None:
        """Valores fuera del sprite se ajustan al borde visible."""
        x, y = resolve_army_position(40, 30, -11, -5)
        self.assertEqual((x, y), (0.0, 0.0))

    def test_respeta_coordenadas_validas(self) -> None:
        """Posiciones explícitas válidas se mantienen."""
        x, y = resolve_army_position(60, 55, 20, 18)
        self.assertEqual((x, y), (20.0, 18.0))


if __name__ == "__main__":
    unittest.main()
