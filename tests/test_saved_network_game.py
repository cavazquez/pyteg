# ruff: noqa: SLF001
"""Cierre de cuatro clientes Qt y reapertura real desde sus archivos guardados."""

from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.conexion.connection import ConnectionClient
from pyteg.gui.dialogs.conectar import VentanaConectar
from pyteg.gui.main_window import Gui
from pyteg.persistence.archive import read_archive
from scripts.smoke_qt_multiclient import (
    _free_port,  # noqa: PLC2701 -- helpers Qt compartidos.
    _wait_for,  # noqa: PLC2701 -- helpers Qt compartidos.
)
from tests.qt_fixtures import dispose_widget

if TYPE_CHECKING:
    from pyteg.client.state_model import ClientStateModel
    from pyteg.server.app import Server


_PLAYERS = 4


class SavedNetworkGameTests(unittest.TestCase):
    """Los archivos recuperan identidades y esperan al resto antes de continuar."""

    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        """Reutiliza la aplicación Qt de la suite."""
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        """Aísla todos los autoguardados y las ventanas."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def _window(self) -> Gui:
        with patch(
            "pyteg.gui.managers.files.QStandardPaths.writableLocation",
            return_value=str(self.directory),
        ):
            window = Gui(Client())
        window.hide()
        window.sound_manager.set_enabled(enabled=False)
        self.addCleanup(dispose_widget, window)
        return window

    def _connect(
        self,
        window: Gui,
        port: int,
        *,
        hosting: bool = False,
        identity: Path | None = None,
    ) -> None:
        dialog = VentanaConectar(window)
        window.ventana_conectar = dialog
        dialog.addr.setText("127.0.0.1")
        dialog.port.setText(str(port))
        dialog.username.setText("Participante")
        if hosting:
            dialog.mode_selector.setCurrentIndex(1)
        elif identity is not None:
            with patch(
                "pyteg.gui.dialogs.conectar.dialog.QFileDialog.getOpenFileName",
                return_value=(str(identity), ""),
            ):
                dialog._restore_identity()
        dialog.connect_to_server()

    def _server(self, window: Gui) -> Server:
        self.assertIsNotNone(window.host_runtime)
        runtime = window.host_runtime
        self.assertIsNotNone(runtime.server if runtime else None)
        return cast("Server", runtime.server if runtime else None)

    @staticmethod
    def _model(window: Gui) -> ClientStateModel:
        return cast("ClientStateModel", window.client_state_model)

    @staticmethod
    def _checkpoint(window: Gui) -> dict[str, Any]:
        runtime = window.host_runtime
        return runtime.latest_checkpoint() or {} if runtime else {}

    @staticmethod
    def _seed(server: Server) -> None:
        game = server.game
        if game is not None:
            country = next(
                name
                for name in server.mapa.paises()
                if server.mapa.ocupado_por(name) == 1
            )
            server.mapa.agregar_misil(country)
            for player in server.dame_clientes():
                game.mazo().asignar_tarjeta(player)
                server.enviar_tarjetas_jugador(player)
            server.bump_state_revision()
            server.enviar_snapshot()

    def test_reopen_after_every_client_closed_restores_all_players(self) -> None:
        """Mapa clásico, reglas de revancha y datos privados sobreviven al cierre."""
        windows = [self._window() for _index in range(4)]
        port = _free_port()
        self._connect(windows[0], port, hosting=True)
        for window in windows[1:]:
            self._connect(window, port)
        _wait_for(
            self.app,
            lambda: all(
                len(self._checkpoint(window).get("peers", [])) == _PLAYERS
                for window in windows
            ),
            15,
            "cuatro copias de sala",
        )
        server = self._server(windows[0])
        windows[0].transmisor.empezar(
            segundos=90,
            paises_para_victoria=0,
            objetivos_secretos=True,
            misiles_habilitados=True,
            rules_profile="revancha",
        )
        _wait_for(self.app, server.estado.es_esperando_jugadores, 10, "configuración")
        windows[0].transmisor.empezar_partida()
        _wait_for(self.app, server.estado.es_jugando, 10, "inicio")
        server.serialized(lambda: self._seed(server))
        _wait_for(
            self.app,
            lambda: all(
                self._model(window).private_cards
                and any(
                    country["misiles"]
                    for country in self._model(window).snapshot["countries"].values()
                )
                for window in windows
            ),
            10,
            "tarjetas y misil",
        )
        countries = deepcopy(server.public_snapshot()["countries"])
        private = [
            (
                deepcopy(self._model(window).private_cards),
                deepcopy(self._model(window).private_objective),
            )
            for window in windows
        ]
        identities = [window.client.userid() for window in windows]
        paths = [self.directory / f"jugador-{index}.pyteg" for index in range(4)]
        for window, path in zip(windows, paths, strict=True):
            if window.host_runtime is not None:
                window.host_runtime.save_game(path)
        room = self._checkpoint(windows[0])["session_id"]
        for window in windows:
            window.close()
        self.app.processEvents()

        reopened = [self._window() for _index in range(4)]
        reopened[0].files_manager.open_path(str(paths[0]))
        restored = self._server(reopened[0])
        _wait_for(
            self.app,
            lambda: (
                reopened[0].client.userid() == identities[0]
                and bool(self._checkpoint(reopened[0]))
            ),
            10,
            "identidad del anfitrión",
        )
        self.assertTrue(
            reopened[0].host_runtime.restored_waiting
            if reopened[0].host_runtime
            else False
        )
        self.assertIsNone(restored._game_coordinator.turno_timer())
        connection = reopened[0].conexion
        self.assertIsNotNone(connection)
        if isinstance(connection, ConnectionClient):
            port = connection.endpoint()[1]
        for window, path in zip(reopened[1:], paths[1:], strict=True):
            self._connect(window, port, identity=path)
        _wait_for(
            self.app,
            lambda: (
                not restored.host_migrating
                and all(self._model(window).private_cards for window in reopened)
            ),
            15,
            "reanudación con todos los jugadores",
        )
        self.assertEqual([window.client.userid() for window in reopened], identities)
        self.assertEqual(restored.public_snapshot()["countries"], countries)
        self.assertEqual(restored.rules_profile, "revancha")
        self.assertEqual(restored.theme, "classic")
        self.assertIsNotNone(restored._game_coordinator.turno_timer())
        self.assertNotEqual(self._checkpoint(reopened[0])["session_id"], room)
        for window, expected in zip(reopened, private, strict=True):
            model = self._model(window)
            self.assertEqual((model.private_cards, model.private_objective), expected)
        self.assertEqual(
            read_archive(paths[0])["payload"]["envelope"]["checkpoint"]["rules"][
                "theme"
            ],
            "revancha",
        )
