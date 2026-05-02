"""Tests ligeros de `gui_toolbar_size` sin toolbar real."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui_toolbar_size import predefined_window_size_rows


class TestGuiToolbarSize(unittest.TestCase):
    """Filas de tamaños predefinidos."""

    def test_predefined_window_size_rows_tres_entradas(self) -> None:
        rows = predefined_window_size_rows()
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(len(row), 4)
            text, w, h, icon = row
            self.assertIsInstance(text, str)
            self.assertIsInstance(w, int)
            self.assertIsInstance(h, int)
            self.assertTrue(icon.endswith(".png"))
