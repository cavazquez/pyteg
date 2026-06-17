"""Tests de estado de gameplay (turno del jugador local)."""

# ruff: noqa: D102, PLC0415, FBT003

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.gui.gameplay_state import es_mi_turno, refresh_acciones_juego


class GameplayStateTests(unittest.TestCase):
    """Pruebas de es_mi_turno y refresh de toolbar."""

    def test_es_mi_turno_cuando_coincide_userid(self) -> None:
        main_window = MagicMock()
        main_window.client.userid.return_value = 2
        main_window.jugador_actual_id = 2
        self.assertTrue(es_mi_turno(main_window))

    def test_no_es_mi_turno_con_otro_jugador(self) -> None:
        main_window = MagicMock()
        main_window.client.userid.return_value = 1
        main_window.jugador_actual_id = 2
        self.assertFalse(es_mi_turno(main_window))

    def test_refresh_deshabilita_finalizar_fuera_de_turno(self) -> None:
        from PySide6.QtWidgets import QApplication, QMainWindow

        from pyteg.gui.toolbar.toolbar import ToolBar

        app = QApplication.instance() or QApplication([])
        del app

        window = QMainWindow()
        main_window = MagicMock()
        main_window.client.userid.return_value = 1
        main_window.jugador_actual_id = 2
        main_window.scene = None
        main_window.findChildren = window.findChildren

        toolbar = ToolBar("test", main_window)
        window.addToolBar(toolbar)
        toolbar.button_finalizar_turno = MagicMock()

        refresh_acciones_juego(main_window)
        toolbar.actualizar_botones_turno(es_mi_turno=False)
        toolbar.button_finalizar_turno.setEnabled.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
