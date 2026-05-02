"""Smoke: el diálogo de tarjetas es importable por el paquete nuevo y por el shim."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui_tarjetas import TarjetasDialog as TarjetasDialogPkg
from pyteg.gui_tarjetas_dialog import TarjetasDialog as TarjetasDialogShim


class TestGuiTarjetasImport(unittest.TestCase):
    """Misma clase desde `gui_tarjetas` y desde `gui_tarjetas_dialog`."""

    def test_mismo_objeto_clase(self) -> None:
        self.assertIs(TarjetasDialogPkg, TarjetasDialogShim)


if __name__ == "__main__":
    unittest.main()
