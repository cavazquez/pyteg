"""Tests de ClientTaskVictoria: mensaje distinto para ganador y perdedor."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyteg.client.tasks.game_flow.partida import ClientTaskVictoria
from tests.locale_fixtures import use_spanish


class ClientTaskVictoriaTests(unittest.TestCase):
    """Comprueba sonido y textos según si el jugador local ganó."""

    @classmethod
    def setUpClass(cls) -> None:
        use_spanish()

    def _main_window(self, userid: int) -> MagicMock:
        main_window = MagicMock()
        main_window.client.userid.return_value = userid
        main_window.chat = None
        return main_window

    @patch("pyteg.client.tasks.game_flow.partida.QMessageBox")
    def test_ganador_ve_felicitaciones(self, mock_msgbox_cls: MagicMock) -> None:
        task = ClientTaskVictoria({
            "mensaje": "victoria",
            "ganador_id": 2,
            "ganador_nombre": "Ana",
        })
        main_window = self._main_window(2)

        task.run(main_window)

        main_window.sound_manager.play_victory.assert_called_once()
        main_window.sound_manager.play_defeat.assert_not_called()
        mock_msgbox = mock_msgbox_cls.return_value
        self.assertIn("Felicitaciones", mock_msgbox.setText.call_args[0][0])

    @patch("pyteg.client.tasks.game_flow.partida.QMessageBox")
    def test_perdedor_ve_derrota(self, mock_msgbox_cls: MagicMock) -> None:
        task = ClientTaskVictoria({
            "mensaje": "victoria",
            "ganador_id": 2,
            "ganador_nombre": "Ana",
        })
        main_window = self._main_window(1)

        task.run(main_window)

        main_window.sound_manager.play_defeat.assert_called_once()
        main_window.sound_manager.play_victory.assert_not_called()
        mock_msgbox = mock_msgbox_cls.return_value
        self.assertIn("perdido", mock_msgbox.setText.call_args[0][0].lower())
