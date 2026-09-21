"""Regresiones visuales mínimas para la tarjeta de país."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from typing import cast

from PySide6.QtWidgets import QApplication

from pyteg.config import CARD_SYMBOL_SIZE, CARD_WIDGET_HEIGHT, CARD_WIDGET_WIDTH
from pyteg.gui.widgets.tarjeta import TarjetaWidget


class TarjetaWidgetTests(unittest.TestCase):
    """Comprueba que el símbolo y el contenedor conservan un tamaño legible."""

    _app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        existing_app = QApplication.instance()
        cls._app = (
            cast("QApplication", existing_app)
            if existing_app is not None
            else QApplication([])
        )

    def test_simbolo_y_tarjeta_tienen_tamanos_legibles(self) -> None:
        tarjeta = TarjetaWidget("Argentina", "Galeon")

        pixmap = tarjeta.label_simbolo.pixmap()
        if pixmap is None:
            self.fail("La tarjeta debe cargar el símbolo de Galeón")
        self.assertEqual(pixmap.height(), CARD_SYMBOL_SIZE)
        self.assertEqual(tarjeta.width(), CARD_WIDGET_WIDTH)
        self.assertEqual(tarjeta.height(), CARD_WIDGET_HEIGHT)


if __name__ == "__main__":
    unittest.main()
