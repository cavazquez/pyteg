"""Smoke: el diálogo de tarjetas es importable desde el paquete canónico."""

# ruff: noqa: D102

from __future__ import annotations

import unittest

from pyteg.gui.tarjetas import TarjetasDialog as TarjetasDialogFromInit
from pyteg.gui.tarjetas.dialog import TarjetasDialog as TarjetasDialogFromModule


class TestGuiTarjetasImport(unittest.TestCase):
    """Misma clase desde `__init__` del paquete y desde `dialog.py`."""

    def test_mismo_objeto_clase(self) -> None:
        self.assertIs(TarjetasDialogFromInit, TarjetasDialogFromModule)


if __name__ == "__main__":
    unittest.main()
