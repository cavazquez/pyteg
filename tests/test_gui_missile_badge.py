"""Pruebas del indicador visual de misiles en un país del mapa."""

# ruff: noqa: SLF001

from __future__ import annotations

import unittest
from typing import ClassVar, cast

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)

from pyteg.gui.mapa.pais_battle_fx_mixin import PaisBattleFxMixin


class _Pais(PaisBattleFxMixin, QGraphicsPixmapItem):
    def __init__(self) -> None:
        super().__init__()
        self._nombre = "Argentina"
        self._army_x = 30.0
        self._army_y = 60.0
        self._misiles_badge = None
        self._misiles_text = None
        self._cantidad_misiles = 0


class MissileBadgeTests(unittest.TestCase):
    """Comprueba el contraste y el ciclo visible del marcador de misil."""

    _app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        """Inicializa Qt para poder crear elementos gráficos."""
        cls._app = cast("QApplication", QApplication.instance() or QApplication([]))

    def test_badge_contrasta_y_muestra_la_cantidad(self) -> None:
        """Muestra icono y cantidad en una placa contrastante."""
        pais = _Pais()

        pais.actualizar_misiles(1)

        badge = cast("QGraphicsRectItem", pais._misiles_badge)
        text = cast("QGraphicsTextItem", pais._misiles_text)
        self.assertEqual(text.toPlainText(), "🚀 1")
        self.assertEqual(badge.brush().color().name(), "#9f1d16")
        self.assertEqual(text.defaultTextColor().name(), "#ffffff")
        self.assertGreater(
            badge.rect().width(),
            text.boundingRect().width(),
        )
        self.assertTrue(badge.isVisible())

    def test_badge_se_oculta_sin_misiles_y_reaparece_al_actualizar(self) -> None:
        """Oculta la placa al agotar misiles y vuelve a mostrarla al reponer."""
        pais = _Pais()
        pais.actualizar_misiles(2)
        badge = cast("QGraphicsRectItem", pais._misiles_badge)
        text = cast("QGraphicsTextItem", pais._misiles_text)

        pais.actualizar_misiles(0)

        self.assertFalse(badge.isVisible())
        self.assertFalse(text.isVisible())

        pais.actualizar_misiles(3)

        self.assertTrue(badge.isVisible())
        self.assertTrue(text.isVisible())
        self.assertEqual(text.toPlainText(), "🚀 3")


if __name__ == "__main__":
    unittest.main()
