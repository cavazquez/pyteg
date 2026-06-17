"""Tests de detección de superposiciones en el layout del mapa."""

from __future__ import annotations

import unittest
from pathlib import Path

from pyteg.gui.mapa.overlap_check import BboxOverlap, PaisBounds, find_bbox_overlaps


class TestMapOverlapCheck(unittest.TestCase):
    """Intersección de bounding boxes entre países."""

    _DUMMY = Path()

    def test_sin_solapamiento(self) -> None:
        """Rectángulos separados no generan pares."""
        bounds = [
            PaisBounds("A", "C1", 0, 0, 10, 10, 0, self._DUMMY),
            PaisBounds("B", "C1", 20, 0, 10, 10, 1, self._DUMMY),
        ]
        self.assertEqual(find_bbox_overlaps(bounds), [])

    def test_solapamiento_y_orden_z(self) -> None:
        """El país con z_index mayor queda como 'encima'."""
        bounds = [
            PaisBounds("Abajo", "C1", 0, 0, 20, 20, 0, self._DUMMY),
            PaisBounds("Arriba", "C2", 10, 10, 20, 20, 1, self._DUMMY),
        ]
        overlaps = find_bbox_overlaps(bounds)
        self.assertEqual(len(overlaps), 1)
        overlap = overlaps[0]
        self.assertIsInstance(overlap, BboxOverlap)
        self.assertEqual(overlap.top.name, "Arriba")
        self.assertEqual(overlap.bottom.name, "Abajo")
        self.assertEqual(overlap.area, 100.0)


if __name__ == "__main__":
    unittest.main()
