"""Inicio común, bots Qt, arrastrar archivos y vista previa de turnos."""

# ruff: noqa: D102, SLF001

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import patch

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog
from shiboken6.Shiboken import isValid

from pyteg.client.app import Client
from pyteg.client.bots import BasicBotStrategy
from pyteg.client.offline import OfflineConnection
from pyteg.gui.dialogs.exported_file import ExportedFileDialog
from pyteg.gui.dialogs.start import StartDialog
from pyteg.gui.dialogs.turn_preview import TurnPreviewDialog
from pyteg.gui.main_window import Gui
from pyteg.persistence.archive import write_archive
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.local import LocalGame
from pyteg.persistence.turn_preview import TurnPreview
from pyteg.toml_reader import TomlReader
from tests.qt_fixtures import dispose_widget
from tests.test_game_archives import complete_turn


class StartScreenTests(unittest.TestCase):
    """Usa widgets reales y archivos aislados del perfil del usuario."""

    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        with patch(
            "pyteg.gui.managers.files.QStandardPaths.writableLocation",
            return_value=str(self.directory),
        ):
            self.window = Gui(Client())
        self.addCleanup(dispose_widget, self.window)

    def _local(self) -> OfflineConnection:
        self.window.files_manager.start_offline("classic", "classic", "Humano", 3)
        self.app.processEvents()
        connection = self.window.conexion
        self.assertIsInstance(connection, OfflineConnection)
        return cast("OfflineConnection", connection)

    def _turn(self) -> dict[str, object]:
        session = AsyncGame.create("revancha", ["Uno", "Dos"])
        self.addCleanup(session.close)
        session.apply({"mensaje": "empezar", "paises_para_victoria": 0})
        session.apply({"mensaje": "empezar_partida"})
        return complete_turn(session)

    def test_start_selects_local_map_and_independent_rules(self) -> None:
        self.window.abrir_ventana_conectar()
        dialog = self.window.files_manager.start_dialog
        self.assertIsInstance(dialog, StartDialog)
        if dialog is None:
            return
        dialog.theme_selector.setCurrentIndex(1)
        dialog.rules_selector.setCurrentIndex(0)
        dialog.name.setText("Humano")
        dialog._start()
        self.app.processEvents()
        connection = cast("OfflineConnection", self.window.conexion)
        self.assertIsInstance(connection.game, LocalGame)
        if connection.game:
            self.assertEqual(connection.game.server.theme, "revancha")
            self.assertEqual(
                connection.game.server.public_snapshot()["configuracion"][
                    "rules_profile"
                ],
                "classic",
            )
        self.assertFalse(dialog.isVisible())
        self.assertTrue(self.window.client.es_admin())

    def test_start_async_and_one_player(self) -> None:
        dialog = StartDialog(self.window)
        dialog.mode.setCurrentIndex(dialog.mode.findData("async"))
        dialog.names.setText("Solo")
        dialog._start()
        self.app.processEvents()
        connection = cast("OfflineConnection", self.window.conexion)
        self.assertIsInstance(connection.game, AsyncGame)
        if connection.game:
            self.assertEqual(len(connection.game.server.dame_clientes()), 1)

    def test_start_lan_preserves_map_rules_and_username(self) -> None:
        dialog = StartDialog(self.window)
        dialog.mode.setCurrentIndex(dialog.mode.findData("lan"))
        dialog.theme_selector.setCurrentIndex(dialog.theme_selector.findData("classic"))
        dialog.rules_selector.setCurrentIndex(
            dialog.rules_selector.findData("revancha")
        )
        dialog.name.setText("Jugador LAN")
        with patch("pyteg.gui.dialogs.conectar.dialog.RoomBrowser") as browser:
            browser.return_value.catalog.rooms.return_value = []
            dialog._start()
        connection_dialog = self.window.ventana_conectar
        self.assertIsNotNone(connection_dialog)
        if connection_dialog is not None:
            self.assertEqual(connection_dialog.theme_selector.currentData(), "classic")
            self.assertEqual(connection_dialog.rules_selector.currentData(), "revancha")
            self.assertEqual(connection_dialog.username.text(), "Jugador LAN")
            self.assertTrue(connection_dialog.isVisible())
        self.assertIsNone(self.window.conexion)

    def test_invalid_local_name_keeps_start_open(self) -> None:
        dialog = StartDialog(self.window)
        dialog.show()
        dialog.name.clear()
        dialog._start()
        self.assertTrue(dialog.isVisible())
        self.assertTrue(dialog.error_label.text())
        self.assertIsNone(self.window.conexion)

    def test_local_bots_advance_and_closing_stops_timer(self) -> None:
        connection = self._local()
        self.window.transmisor.empezar(segundos=3600, paises_para_victoria=0)
        self.window.transmisor.empezar_partida()
        self.app.processEvents()

        game = cast("LocalGame", connection.game)
        strategy = BasicBotStrategy(TomlReader.from_theme("classic"))
        while connection.state_model.snapshot["fase"] == "colocacion":
            command = strategy.next_command(connection.state_model)
            self.assertIsNotNone(command)
            if command:
                game.apply(command)
            self.app.processEvents()
        game.apply({"mensaje": "finalizar_turno"})
        connection._bot_timer.setInterval(1)
        for _wait in range(100):
            QTest.qWait(10)
            if game.holder() == game.user_id:
                break
        self.assertEqual(game.holder(), game.user_id)
        self.window.files_manager.refresh()
        self.assertFalse(self.window.files_manager.actions["export_turn"].isEnabled())
        self.window.close()
        self.assertFalse(connection._bot_timer.isActive())
        self.app.processEvents()

    def test_battle_timer_is_owned_by_country_effect(self) -> None:
        self.assertIsNotNone(self.window.scene)
        if self.window.scene is None:
            return
        country = next(iter(self.window.scene.paises.values()))
        country.iniciar_titilacion_batalla()
        timer = country._titilacion_timer
        self.assertIsNotNone(timer)
        if timer is not None:
            self.assertIs(timer.parent(), country._titilacion_effect)
        dispose_widget(self.window)
        self.assertFalse(isValid(timer))

    def test_floating_loss_timers_are_owned_by_the_effect(self) -> None:
        self.assertIsNotNone(self.window.scene)
        if self.window.scene is None:
            return
        country = next(iter(self.window.scene.paises.values()))
        country.mostrar_perdida_flotante(1)
        timer = country._movimiento_timer
        animation = country._opacity_animation
        self.assertIsNotNone(timer)
        self.assertIsNotNone(animation)
        if timer is not None and animation is not None:
            self.assertIs(timer.parent(), animation.parent())
            self.assertIs(animation.parent(), animation.targetObject())
        dispose_widget(self.window)
        self.assertFalse(isValid(timer))
        self.assertFalse(isValid(animation))

    def test_recent_local_save_reopens_with_bots(self) -> None:
        connection = self._local()
        path = self.directory / "local.pyteg"
        if connection.game:
            write_archive(path, connection.game.draft())
        self.window.files_manager._remember(path)
        connection.desconectar()
        self.window.files_manager.show_start()
        dialog = self.window.files_manager.start_dialog
        self.assertIsNotNone(dialog)
        if dialog is not None:
            self.assertGreater(dialog.recent_list.count(), 0)
        self.assertTrue(self.window.files_manager.open_path(str(path)))
        resumed = cast("OfflineConnection", self.window.conexion)
        self.assertIsInstance(resumed.game, LocalGame)

    def test_cancel_preview_preserves_connection_and_map(self) -> None:
        path = self.directory / "turn.pyturn"
        write_archive(path, self._turn())
        with patch.object(
            TurnPreviewDialog, "exec", return_value=QDialog.DialogCode.Rejected
        ):
            self.assertFalse(
                self.window.files_manager.open_path(str(path), preview=True)
            )
        self.assertIsNone(self.window.conexion)
        self.assertEqual(self.window.map_theme, "classic")

    def test_accepted_preview_imports_and_keeps_new_recipient(self) -> None:
        path = self.directory / "turn.pyturn"
        write_archive(path, self._turn())
        with patch.object(
            TurnPreviewDialog, "exec", return_value=QDialog.DialogCode.Accepted
        ):
            self.assertTrue(
                self.window.files_manager.open_path(str(path), preview=True)
            )
        self.app.processEvents()
        self.assertEqual(self.window.client.userid(), 2)
        self.assertEqual(self.window.map_theme, "revancha")

    def test_drop_uses_preview_flow(self) -> None:
        data = QMimeData()
        data.setUrls([QUrl.fromLocalFile(str(self.directory / "turn.pyturn"))])
        drag = QDragEnterEvent(
            QPoint(1, 1),
            Qt.DropAction.CopyAction,
            data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.window.dragEnterEvent(drag)
        self.assertTrue(drag.isAccepted())
        drop = QDropEvent(
            QPointF(1, 1),
            Qt.DropAction.CopyAction,
            data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        with patch.object(
            self.window.files_manager, "open_path", return_value=True
        ) as opened:
            self.window.dropEvent(drop)
            opened.assert_called_once_with(
                str(self.directory / "turn.pyturn"), preview=True
            )
        self.assertTrue(drop.isAccepted())

    def test_export_copies_exact_path_and_offers_folder(self) -> None:
        path = self.directory / "share.pyturn"
        dialog = ExportedFileDialog(path, self.window)
        dialog._copy()
        self.assertEqual(self.app.clipboard().text(), str(path.resolve()))
        with patch(
            "pyteg.gui.dialogs.exported_file.QDesktopServices.openUrl"
        ) as opened:
            dialog._folder()
            opened.assert_called_once_with(QUrl.fromLocalFile(str(self.directory)))

    def test_preview_lists_author_and_recipient_without_secrets(self) -> None:
        dialog = TurnPreviewDialog(TurnPreview.from_archive(self._turn()), self.window)
        self.assertIn("Uno", dialog.summary.text())
        self.assertIn("Dos", dialog.summary.text())
        self.assertNotIn("token", dialog.summary.text())


if __name__ == "__main__":
    unittest.main()
