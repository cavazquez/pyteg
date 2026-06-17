"""Tests de `LanguageManager` con mocks de la ventana principal."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

from pyteg.gui.managers.language import LanguageManager

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class TestLanguageManager(unittest.TestCase):
    """Refresco de textos al cambiar idioma."""

    def setUp(self) -> None:
        """Host mínimo con barra de estado y paneles laterales."""
        self.toolbar = MagicMock()
        self.players_title = MagicMock()
        self.units_title = MagicMock()
        self.units_manager = MagicMock()
        self.main_window = SimpleNamespace(
            setWindowTitle=MagicMock(),
            mi_jugador_text=MagicMock(),
            estado_label=MagicMock(text=MagicMock(return_value="Estado: X")),
            turno_label=MagicMock(text=MagicMock(return_value="Turno: 1")),
            scene=None,
            toolbar=self.toolbar,
            players_title_label=self.players_title,
            units_section_title_label=self.units_title,
            units_manager=self.units_manager,
        )
        self.manager = LanguageManager(cast("MainWindowProtocol", self.main_window))

    @patch("pyteg.gui.managers.language.QApplication.topLevelWidgets", return_value=[])
    def test_on_language_changed_actualiza_paneles(
        self, _mock_top_level: MagicMock
    ) -> None:
        """Actualiza toolbar, títulos laterales y filas de unidades."""
        self.manager.on_language_changed("en")

        self.main_window.setWindowTitle.assert_called_once()
        self.toolbar.update_language.assert_called_once_with("en")
        self.players_title.setText.assert_called_once()
        self.units_title.setText.assert_called_once()
        self.units_manager.refresh_unit_labels.assert_called_once()


if __name__ == "__main__":
    unittest.main()
