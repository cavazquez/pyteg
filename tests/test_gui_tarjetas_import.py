"""Smoke: el diálogo de tarjetas es importable desde el paquete canónico."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QWidget

from pyteg.client.state_model import ClientStateModel
from pyteg.gui.tarjetas import TarjetasDialog as TarjetasDialogFromInit
from pyteg.gui.tarjetas.dialog import TarjetasDialog as TarjetasDialogFromModule
from tests.qt_fixtures import dispose_widget


class _CardHost(QWidget):
    """Padre con reglas públicas y transmisor observable."""

    def __init__(self) -> None:
        super().__init__()
        self.map_theme = "revancha"
        self.client_state_model = ClientStateModel()
        self.client_state_model.rules = {
            "cards_for_exchange": 3,
            "continent_card_exchanges": {
                "Asia": [],
                "AmericaDelSur": ["Avion", "Tanque"],
            },
        }
        self.transmisor = MagicMock()


class TestGuiTarjetasImport(unittest.TestCase):
    """Misma clase desde `__init__` del paquete y desde `dialog.py`."""

    def test_mismo_objeto_clase(self) -> None:
        self.assertIs(TarjetasDialogFromInit, TarjetasDialogFromModule)


class TestGuiCardExchanges(unittest.TestCase):
    """El diálogo distingue las equivalencias del canje por país propio."""

    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        self.host = _CardHost()
        self.addCleanup(dispose_widget, self.host)
        self.dialog = TarjetasDialogFromModule(self.host)

    def test_full_continent_uses_general_exchange(self) -> None:
        self.dialog.actualizar_tarjetas([
            {
                "pais": "continente:Asia",
                "simbolo": "Continente",
                "tipo": "continente",
                "continente": "Asia",
            }
        ])
        self.dialog.seleccionar_todas()
        self.assertTrue(self.dialog.button_canje.isEnabled())
        self.dialog.realizar_canje()
        self.host.transmisor.canjear_tarjetas.assert_called_once()
        self.host.transmisor.canje_especial.assert_not_called()

    def test_small_continent_and_wildcard_use_general_exchange(self) -> None:
        self.dialog.actualizar_tarjetas([
            {
                "pais": "continente:AmericaDelSur",
                "simbolo": "Continente",
                "tipo": "continente",
                "continente": "AmericaDelSur",
            },
            {"pais": "Carta", "simbolo": "Soldado", "tipo": "pais"},
        ])
        self.dialog.seleccionar_todas()
        self.assertTrue(self.dialog.button_canje.isEnabled())
        self.dialog.realizar_canje()
        self.host.transmisor.canjear_tarjetas.assert_called_once()

    def test_country_alone_preserves_special_exchange(self) -> None:
        self.dialog.actualizar_tarjetas([
            {"pais": "Argentina", "simbolo": "Avion", "tipo": "pais"}
        ])
        self.dialog.seleccionar_todas()
        self.dialog.realizar_canje()
        self.host.transmisor.canje_especial.assert_called_once_with("Argentina")
        self.host.transmisor.canjear_tarjetas.assert_not_called()

    def test_incomplete_continent_selection_is_disabled(self) -> None:
        self.dialog.actualizar_tarjetas([
            {
                "pais": "continente:AmericaDelSur",
                "simbolo": "Continente",
                "tipo": "continente",
                "continente": "AmericaDelSur",
            }
        ])
        self.dialog.seleccionar_todas()
        self.assertFalse(self.dialog.button_canje.isEnabled())

    def test_refresh_clears_stale_card_selection(self) -> None:
        self.dialog.seleccionar_todas()
        self.dialog.actualizar_tarjetas([])
        self.assertEqual(self.dialog.tarjetas_seleccionadas, [])
        self.assertFalse(self.dialog.button_canje.isEnabled())


if __name__ == "__main__":
    unittest.main()
