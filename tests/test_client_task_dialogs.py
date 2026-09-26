"""Regresiones de los avisos recibidos desde eventos de red."""

# ruff: noqa: D102

from __future__ import annotations

import logging
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt

from pyteg.client.tasks.dialogs import open_message_box
from pyteg.client.tasks.game_flow.partida import ClientTaskVictoria
from pyteg.client.tasks.lobby.chat import ClientTaskError
from pyteg.logger.manager import PyTegLogger


class ClientTaskDialogTests(unittest.TestCase):
    """Los avisos dejan libre el bucle de eventos y difieren sus callbacks."""

    def test_open_message_box_difiere_callback_hasta_finished(self) -> None:
        dialog = MagicMock()
        on_finished = MagicMock()

        open_message_box(dialog, on_finished=on_finished)

        dialog.setAttribute.assert_called_once_with(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.open.assert_called_once_with()
        dialog.exec.assert_not_called()
        on_finished.assert_not_called()

        dialog.finished.connect.assert_called_once()
        callback = dialog.finished.connect.call_args.args[0]
        callback(0)
        on_finished.assert_called_once_with()

    @patch("pyteg.client.tasks.game_flow.partida.QMessageBox")
    def test_victoria_actualiza_chat_antes_de_abrir_aviso(
        self, message_box_cls: MagicMock
    ) -> None:
        main_window = MagicMock()
        main_window.client.userid.return_value = 2
        events: list[str] = []
        main_window.chat.append.side_effect = lambda *_args: events.append("chat")
        dialog = message_box_cls.return_value
        dialog.open.side_effect = lambda: events.append("open")

        ClientTaskVictoria({
            "mensaje": "victoria",
            "ganador_id": 2,
            "ganador_nombre": "Ana",
        }).run(main_window)

        self.assertEqual(events, ["chat", "open"])
        main_window.sound_manager.play_victory.assert_called_once_with()
        main_window.chat.append.assert_called_once()
        self.assertIn("Ana", main_window.chat.append.call_args.args[0])
        dialog.open.assert_called_once_with()
        dialog.exec.assert_not_called()
        dialog.finished.connect.assert_not_called()

    def test_errores_de_reconexion_esperan_a_cerrar_el_aviso(self) -> None:
        for error_type in (
            "incompatible_theme",
            "reconnect_rejected",
            "duplicate_username",
        ):
            with (
                self.subTest(error_type=error_type),
                patch("pyteg.client.tasks.lobby.chat.QMessageBox") as message_box_cls,
            ):
                main_window = MagicMock()
                main_window.client_state_model.theme = "classic"

                ClientTaskError({
                    "mensaje": "error",
                    "error_type": error_type,
                    "message": "No se pudo conectar",
                }).run(main_window)

                dialog = message_box_cls.return_value
                dialog.open.assert_called_once_with()
                dialog.exec.assert_not_called()
                main_window.abrir_ventana_conectar.assert_not_called()
                dialog.finished.connect.assert_called_once()

                callback = dialog.finished.connect.call_args.args[0]
                callback(0)
                main_window.abrir_ventana_conectar.assert_called_once_with()

                if error_type == "incompatible_theme":
                    main_window.conexion.abortar.assert_called_once_with()
                elif error_type == "reconnect_rejected":
                    main_window.client.reset_session.assert_called_once_with()
                    main_window.client_by_id.clear.assert_called_once_with()
                else:
                    main_window.conexion.desconectar.assert_called_once_with()

    @patch("pyteg.client.tasks.lobby.chat.QMessageBox")
    def test_error_generico_no_instala_callback(
        self, message_box_cls: MagicMock
    ) -> None:
        main_window = MagicMock()

        ClientTaskError({
            "mensaje": "error",
            "error_type": "invalid_command",
            "message": "Comando inválido",
        }).run(main_window)

        dialog = message_box_cls.return_value
        dialog.open.assert_called_once_with()
        dialog.exec.assert_not_called()
        dialog.finished.connect.assert_not_called()


class LoggerPropagationTests(unittest.TestCase):
    """Los loggers gestionados no duplican registros en sus padres."""

    @patch.object(PyTegLogger, "_setup_directories")
    @patch("pyteg.logger.manager.setup_file_handler")
    @patch("pyteg.logger.manager.setup_console_handler")
    def test_loggers_jerarquicos_no_propagan_al_padre(
        self,
        _console_handler: MagicMock,
        _file_handler: MagicMock,
        _setup_directories: MagicMock,
    ) -> None:
        manager = PyTegLogger()
        parent = manager.get_logger("pyteg.regression_dialogs")
        child = manager.get_logger("pyteg.regression_dialogs.child")

        self.assertFalse(parent.propagate)
        self.assertFalse(child.propagate)
        self.assertEqual(parent.level, logging.DEBUG)
        self.assertEqual(child.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
