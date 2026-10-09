"""Pruebas de estados públicos en la lista lateral de jugadores."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from pyteg.gui.managers.players import PlayersManager, PlayerStatus
from tests.qt_fixtures import dispose_widget


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

    def test_unchanged_snapshot_preserves_visible_player_widgets(self) -> None:
        QApplication.instance() or QApplication([])
        parent = QWidget()
        self.addCleanup(dispose_widget, parent)
        host = SimpleNamespace(
            players_layout=QVBoxLayout(parent), theme_manager=MagicMock()
        )
        manager = PlayersManager(host)
        players = [("Humano", QColor("#ff0000")), ("Bot 1", QColor("#0000ff"))]
        manager.update_player_list(players)
        widgets = list(manager.player_labels)
        manager.update_player_list(players)
        self.assertEqual(manager.player_labels, widgets)
        manager.update_player_statuses([PlayerStatus("Bot 1", eliminated=True)])
        self.assertIn("Eliminado", manager.status_labels["Bot 1"].text())
        manager.update_player_list([])
        self.assertFalse(manager.player_labels)


if __name__ == "__main__":
    unittest.main()
