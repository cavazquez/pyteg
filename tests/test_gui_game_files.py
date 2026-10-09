"""Integración Qt del descubrimiento y de partidas, turnos y repeticiones."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QWidget

from pyteg.client.app import Client
from pyteg.client.offline import OfflineConnection
from pyteg.gui.dialogs.async_setup import AsyncSetupDialog
from pyteg.gui.dialogs.conectar import VentanaConectar
from pyteg.gui.dialogs.replay import ReplayWindow
from pyteg.gui.main_window import Gui
from pyteg.network.discovery import Room
from pyteg.persistence.archive import FileRepository, read_archive, write_archive
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.history import Replay
from pyteg.protocol import map_hash_for_theme
from tests.qt_fixtures import dispose_widget
from tests.test_game_archives import complete_turn


class GuiGameFilesTests(unittest.TestCase):
    """Usa widgets reales con todos los guardados aislados en un directorio."""

    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        """Comparte la aplicación Qt con las demás pruebas."""
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        """Crea una ventana y un repositorio temporal."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        with patch(
            "pyteg.gui.managers.files.QStandardPaths.writableLocation",
            return_value=str(self.directory),
        ):
            self.window = Gui(Client())
        self.addCleanup(dispose_widget, self.window)
        self.repository = FileRepository(self.directory / "async.pyteg")

    def _offline(self) -> OfflineConnection:
        connection = OfflineConnection(self.window)
        connection.create("classic", ["Uno", "Dos", "Tres", "Cuatro"], self.repository)
        self.window.reset_session_state()
        connection.conectar()
        self.window.transmisor.empezar(paises_para_victoria=0)
        self.window.transmisor.empezar_partida()
        self.app.processEvents()
        return connection

    def test_local_transport_projects_identity_and_actions(self) -> None:
        """La interfaz recibe los mismos snapshots y datos privados que TCP."""
        connection = self._offline()
        self.assertEqual(self.window.client.userid(), 1)
        self.assertEqual(self.window.estado_actual, "JUGANDO")
        self.assertEqual(
            self.window.network_status_label.text(), "Partida por archivos"
        )
        self.assertEqual(self.window.timer_label.text(), "Sin límite de tiempo")
        self.assertTrue(self.window.client.es_admin())
        self.assertTrue(connection.esta_conectado())
        self.window.files_manager.refresh()
        self.assertTrue(self.window.files_manager.actions["save"].isEnabled())
        self.assertFalse(self.window.files_manager.actions["export_turn"].isEnabled())
        complete_turn(cast("AsyncGame", connection.game))
        self.window.files_manager.refresh()
        self.assertTrue(self.window.files_manager.actions["export_turn"].isEnabled())

    def test_creation_dialog_selects_map_and_allows_one_player(self) -> None:
        """El mapa se elige en el mismo formulario que los jugadores."""
        dialog = AsyncSetupDialog("revancha", self.window)
        self.assertEqual(dialog.theme_selector.currentData(), "revancha")
        dialog.names.setText("Solo")
        with (
            patch("pyteg.gui.managers.files.AsyncSetupDialog", return_value=dialog),
            patch.object(dialog, "exec", return_value=dialog.DialogCode.Accepted),
        ):
            self.window.files_manager.create_async()
        self.app.processEvents()
        self.assertEqual(self.window.map_theme, "revancha")
        self.assertIsNotNone(self.window.scene)
        if self.window.scene is not None:
            self.assertIs(self.window.scene.parent(), self.window)
        self.assertIsInstance(self.window.w, QWidget)
        if isinstance(self.window.w, QWidget):
            self.assertIs(self.window.w.parent(), self.window)
        connection = self.window.conexion
        self.assertIsInstance(connection, OfflineConnection)
        if isinstance(connection, OfflineConnection) and connection.game:
            self.assertEqual(len(connection.game.server.dame_clientes()), 1)
        dialog.close()

    def test_closing_cancels_pending_offline_and_notice_timers(self) -> None:
        """Cerrar una partida no deja callbacks que actualicen la ventana."""
        connection = self._offline()
        connection.send_data('{"mensaje": "solicitar_snapshot"}')
        self.window.update_status_bar("Aviso pendiente")
        self.assertTrue(connection._availability_timer.isActive())  # noqa: SLF001
        notice = self.window.status_manager._notice_timer  # noqa: SLF001
        self.assertIs(notice.parent(), self.window)
        self.assertTrue(notice.isActive())
        self.window.close()
        self.assertFalse(connection._availability_timer.isActive())  # noqa: SLF001
        self.assertFalse(notice.isActive())
        self.app.processEvents()

    def test_save_and_open_draft_restores_country_state(self) -> None:
        """El menú guarda y vuelve a abrir sin crear un socket."""
        connection = self._offline()
        game = cast("AsyncGame", connection.game)
        path = self.directory / "manual.pyteg"
        with patch(
            "pyteg.gui.managers.files.QFileDialog.getSaveFileName",
            return_value=(str(path), ""),
        ):
            self.window.files_manager.save_game()
        expected = game.server.public_snapshot()["countries"]
        self.assertIn("async", read_archive(path)["payload"])
        connection.desconectar()
        self.window.files_manager.open_path(str(path))
        self.app.processEvents()
        resumed = self.window.conexion
        self.assertIsInstance(resumed, OfflineConnection)
        if isinstance(resumed, OfflineConnection) and resumed.game:
            self.assertEqual(
                resumed.game.server.public_snapshot()["countries"], expected
            )

    def test_import_continuation_keeps_identity_and_rejects_duplicate(self) -> None:
        """Abrir el mismo turno dos veces no vuelve a aplicar el estado."""
        connection = self._offline()
        game = cast("AsyncGame", connection.game)
        packet = complete_turn(game)
        for _step in range(12):
            if packet["payload"]["holder"] == game.user_id:
                break
            following = AsyncGame.open(packet)
            try:
                packet = complete_turn(following)
            finally:
                following.close()
        path = self.directory / "next.pyturn"
        write_archive(path, packet)
        self.window.files_manager.open_path(str(path))
        self.app.processEvents()
        resumed = self.window.conexion
        self.window.files_manager.open_path(str(path))
        self.assertIs(self.window.conexion, resumed)
        self.assertEqual(self.window.client.userid(), game.user_id)

    def test_replay_has_independent_read_only_map(self) -> None:
        """Navegar la repetición no cambia el motor ni usa su transmisor."""
        connection = self._offline()
        game = cast("AsyncGame", connection.game)
        complete_turn(game)
        history = game.server.serialized(game.server.history.export)
        replay = Replay(history)
        dialog = ReplayWindow(replay, self.window)
        self.assertIs(dialog.scene.parent(), dialog)
        dialog.show()
        dialog.seek(replay.count - 1)
        self.assertEqual(dialog.slider.value(), replay.count - 1)
        country = next(iter(dialog.scene.paises))
        self.assertEqual(
            dialog.scene.paises[country].get_unidades(),
            replay.snapshot(replay.count - 1)["countries"][country]["unidades"],
        )
        before = game.server.public_snapshot()
        dialog.seek(0)
        dialog.jump_turn(1)
        self.assertEqual(game.server.public_snapshot(), before)
        self.assertIsNot(dialog.scene, self.window.scene)
        dialog.close()
        self.assertFalse(dialog._fit_timer.isActive())  # noqa: SLF001
        self.assertFalse(dialog._timer.isActive())  # noqa: SLF001

    def test_selecting_discovered_room_loads_address_and_map(self) -> None:
        """Elegir una sala evita escribir su IP, puerto o mapa."""
        with patch(
            "pyteg.gui.dialogs.conectar.dialog.RoomBrowser",
            side_effect=OSError("sin UDP"),
        ):
            dialog = VentanaConectar(self.window)
        room = Room(
            "room",
            1,
            "Nueva sala",
            "revancha",
            map_hash_for_theme("revancha"),
            "192.168.1.30",
            40000,
            4,
            "JUGANDO",
        )
        dialog.room_selector.addItem("Nueva sala", room)
        dialog.room_selector.setCurrentIndex(1)
        self.assertEqual(dialog.addr.text(), room.host)
        self.assertEqual(dialog.port.text(), str(room.port))
        self.assertEqual(dialog.theme_selector.currentData(), "revancha")
        dialog.reject()
