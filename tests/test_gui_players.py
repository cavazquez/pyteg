"""Pruebas de estados públicos en la lista lateral de jugadores."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from pyteg.gui.managers.players import PlayersManager, PlayerStatus


class PlayersManagerStatusTests(unittest.TestCase):
    """La lista muestra estados sin alterar el formato histórico de nombres."""

    def test_muestra_administrador_y_desconexion(self) -> None:
        QApplication.instance() or QApplication([])
        host = SimpleNamespace(players_layout=None, theme_manager=MagicMock())
        manager = PlayersManager(host)
        manager.update_player_list([("Ana", QColor("#ff0000"))])

        manager.update_player_statuses([
            PlayerStatus("Ana", connected=False, admin=True)
        ])

        badge = manager.status_labels["Ana"]
        self.assertIn("Administrador", badge.text())
        self.assertIn("Desconectado", badge.text())


if __name__ == "__main__":
    unittest.main()
