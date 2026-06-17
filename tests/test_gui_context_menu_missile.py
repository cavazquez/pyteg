"""Tests del menú contextual: lanzar misil."""

# ruff: noqa: D102
# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QWidget

from pyteg.gui.mapa.menu.contextual import Menu


class ContextMenuMissileTests(unittest.TestCase):
    """Verifica visibilidad de la acción Lanzar misil."""

    _parent: QWidget

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])
        cls._parent = QWidget()

    def _build_menu(
        self,
        *,
        misiles_habilitados: bool,
        origen: str | None,
        destino: str | None,
        misiles_origen: int,
    ) -> Menu:
        main_window = MagicMock()
        main_window.misiles_habilitados = misiles_habilitados
        main_window.last_units = {}

        pais_origen_widget = MagicMock()
        pais_origen_widget.get_cantidad_misiles.return_value = misiles_origen

        main_window.scene.selection_manager.get_pais_origen.return_value = origen
        main_window.scene.selection_manager.get_pais_destino.return_value = destino
        main_window.scene.paises = {}
        if origen:
            main_window.scene.paises[origen] = pais_origen_widget

        parent = self._parent
        return Menu("Brasil", "Sudamerica", main_window, parent=parent)

    def test_lanzar_misil_visible_con_seleccion_y_misiles(self) -> None:
        menu = self._build_menu(
            misiles_habilitados=True,
            origen="Argentina",
            destino="Brasil",
            misiles_origen=1,
        )
        actions = [action.text() for action in menu.actions()]
        self.assertIn(menu.action_lanzar_misil.text(), actions)

    def test_lanzar_misil_oculto_sin_misiles_en_origen(self) -> None:
        menu = self._build_menu(
            misiles_habilitados=True,
            origen="Argentina",
            destino="Brasil",
            misiles_origen=0,
        )
        actions = [action.text() for action in menu.actions()]
        self.assertNotIn(menu.action_lanzar_misil.text(), actions)


if __name__ == "__main__":
    unittest.main()
