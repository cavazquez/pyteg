"""Tests del diálogo de movimiento de unidades."""

# ruff: noqa: D102, PLC0415
# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QDialog

from pyteg.gui.dialogs.move import MoveDialog


class MoveDialogTests(unittest.TestCase):
    """Pruebas de MoveDialog."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_max_unidades_limits_spinbox(self) -> None:
        dialog = MoveDialog("Argentina", "Brasil", 5)
        self.assertEqual(dialog.spin_box.maximum(), 5)
        self.assertEqual(dialog.get_cantidad_unidades(), 1)

    def test_get_cantidad_after_spin_change(self) -> None:
        dialog = MoveDialog("Argentina", "Brasil", 4)
        dialog.spin_box.setValue(3)
        self.assertEqual(dialog.get_cantidad_unidades(), 3)

    @patch("pyteg.gui.managers.game_actions.MoveDialog")
    def test_mover_cancel_no_llama_transmisor(self, mock_dialog_cls: MagicMock) -> None:
        from pyteg.gui.managers.game_actions import GameActionsManager

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
        mock_dialog_cls.return_value = mock_dialog

        main_window = MagicMock()
        main_window.scene.selection_manager.get_pais_origen.return_value = "Argentina"
        main_window.scene.selection_manager.get_pais_destino.return_value = "Brasil"
        main_window.scene.paises = {
            "Argentina": MagicMock(get_unidades=MagicMock(return_value=4))
        }

        with (
            patch(
                "pyteg.gui.managers.game_actions.cliente_esta_conectado",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.es_mi_turno",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.puede_atacar_o_mover",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.es_mi_pais",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.son_adyacentes",
                return_value=True,
            ),
        ):
            GameActionsManager(main_window).mover()

        main_window.transmisor.mover_unidad.assert_not_called()

    @patch("pyteg.gui.managers.game_actions.MoveDialog")
    def test_mover_accept_envia_cantidad(self, mock_dialog_cls: MagicMock) -> None:
        from pyteg.gui.managers.game_actions import GameActionsManager

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_cantidad_unidades.return_value = 3
        mock_dialog_cls.return_value = mock_dialog

        main_window = MagicMock()
        main_window.scene.selection_manager.get_pais_origen.return_value = "Argentina"
        main_window.scene.selection_manager.get_pais_destino.return_value = "Brasil"
        main_window.scene.paises = {
            "Argentina": MagicMock(get_unidades=MagicMock(return_value=4))
        }

        with (
            patch(
                "pyteg.gui.managers.game_actions.cliente_esta_conectado",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.es_mi_turno",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.puede_atacar_o_mover",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.es_mi_pais",
                return_value=True,
            ),
            patch(
                "pyteg.gui.managers.game_actions.son_adyacentes",
                return_value=True,
            ),
        ):
            GameActionsManager(main_window).mover()

        main_window.transmisor.mover_unidad.assert_called_once_with(
            origen="Argentina", destino="Brasil", cantidad=3
        )


if __name__ == "__main__":
    unittest.main()
