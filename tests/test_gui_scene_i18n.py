"""Tests de i18n en `CountrySelectionManager.refresh_labels` (sin Qt real)."""

# ruff: noqa: D102, SLF001 — métodos privados / accesos a estado interno del manager.

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.gui.mapa.selection_manager import CountrySelectionManager
from tests.locale_fixtures import use_spanish


def _make_manager() -> tuple[CountrySelectionManager, MagicMock]:
    """Construye un `CountrySelectionManager` con `main_window` y `scene` mockeados.

    Returns:
        Tupla ``(manager, main_window_mock)`` para asserts directos sobre el mock.

    """
    main_window = MagicMock()
    main_window.seleccion_label = MagicMock()
    # `findChildren` se usa al notificar a la toolbar: devolvemos lista vacía
    # para que el helper no haga nada.
    main_window.findChildren = MagicMock(return_value=[])
    scene = MagicMock()
    return CountrySelectionManager(main_window, scene), main_window


class TestCountrySelectionManagerRefreshLabels(unittest.TestCase):
    """`refresh_labels` re-aplica las traducciones según el estado de selección."""

    @classmethod
    def setUpClass(cls) -> None:
        use_spanish()

    def test_refresh_labels_sin_seleccion(self) -> None:
        manager, mw = _make_manager()
        manager.refresh_labels()
        mw.seleccion_label.setText.assert_called_once()
        text = mw.seleccion_label.setText.call_args[0][0]
        self.assertIn("Selección", text)
        self.assertIn("origen", text)

    def test_refresh_labels_solo_origen(self) -> None:
        manager, mw = _make_manager()
        manager._pais_origen = "Argentina"
        manager.refresh_labels()
        text = mw.seleccion_label.setText.call_args[0][0]
        self.assertIn("Argentina", text)
        self.assertIn("destino", text)

    def test_refresh_labels_origen_y_destino(self) -> None:
        manager, mw = _make_manager()
        manager._pais_origen = "Argentina"
        manager._pais_destino = "Brasil"
        manager.refresh_labels()
        text = mw.seleccion_label.setText.call_args[0][0]
        self.assertIn("Argentina", text)
        self.assertIn("Brasil", text)
        self.assertIn("Atacar", text)


if __name__ == "__main__":
    unittest.main()
