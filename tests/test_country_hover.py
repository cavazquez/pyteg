"""Regresiones de información contextual de países sin etiquetas permanentes."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast

from PySide6.QtWidgets import QApplication

from pyteg.gui.mapa.scene import QCustomGraphicsScene


class CountryHoverTests(unittest.TestCase):
    """Comprueba que el país siga siendo identificable sin ensuciar el mapa."""

    _app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        existing_app = QApplication.instance()
        cls._app = (
            cast("QApplication", existing_app)
            if existing_app is not None
            else QApplication([])
        )

    def test_tooltip_identifica_pais_continente_y_unidades(self) -> None:
        scene = QCustomGraphicsScene(SimpleNamespace(), theme="test")
        pais = scene.obtener_pais("Rectangulo")
        self.assertIsNotNone(pais)
        if pais is None:
            return

        self.assertIn("País: Rectangulo", pais.toolTip())
        self.assertIn("Continente: Sudamerica", pais.toolTip())
        self.assertIn("Unidades: 0", pais.toolTip())

        pais.set_unidades(7)
        self.assertIn("Unidades: 7", pais.toolTip())


if __name__ == "__main__":
    unittest.main()
