"""Acciones de archivos de partidas, turnos y repeticiones."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from pyteg.client.bot_strategies import DEFAULT_BOT_DIFFICULTY
from pyteg.client.conexion.connection import ConnectionClient
from pyteg.client.conexion.transmisor import ClientTransmisor
from pyteg.client.offline import OfflineConnection
from pyteg.gui.dialogs.async_setup import AsyncSetupDialog
from pyteg.gui.dialogs.exported_file import ExportedFileDialog
from pyteg.gui.dialogs.replay import ReplayWindow
from pyteg.gui.dialogs.start import StartDialog
from pyteg.gui.dialogs.turn_preview import TurnPreviewDialog
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.persistence.archive import (
    FileRepository,
    make_archive,
    read_archive,
    write_archive,
)
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.history import Replay
from pyteg.persistence.recent import RecentGames
from pyteg.persistence.turn_preview import TurnPreview
from pyteg.server.hosting.runtime import HostRuntime

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.gui.main_window import Gui

_LOG = get_logger(__name__)


class GameFilesManager:
    """Coordina diálogos; la persistencia y las reglas viven fuera de Qt."""

    def __init__(self, window: Gui) -> None:
        """Agrega acciones sin ocupar espacio permanente en la toolbar."""
        self.window = window
        self.save_directory = (
            Path(
                QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.GenericDataLocation
                )
            )
            / "pyteg"
            / "autosaves"
        )
        self.repository = FileRepository(
            self.save_directory / f"{uuid.uuid4().hex}.pyteg", session_scoped=True
        )
        self.recent = RecentGames(self.save_directory)
        self.start_dialog: StartDialog | None = None
        self.export_dialog: ExportedFileDialog | None = None
        self.last_export: Path | None = None
        menu = window.menuBar().addMenu(_("Partida"))
        self.menu = menu
        self.actions: dict[str, QAction] = {}
        self._labels: dict[str, str] = {}
        entries: list[
            tuple[str, str, Callable[[], object], QKeySequence.StandardKey | None]
        ] = [
            ("new", "Nueva partida…", self.show_start, QKeySequence.StandardKey.New),
            ("save", "Guardar partida…", self.save_game, QKeySequence.StandardKey.Save),
            (
                "open",
                "Abrir partida o turno…",
                self.open_game,
                QKeySequence.StandardKey.Open,
            ),
            ("async", "Nueva partida por archivos…", self.create_async, None),
            ("export_turn", "Exportar turno…", self.export_turn, None),
            (
                "export_folder",
                "Abrir carpeta de exportaciones",
                self.open_export_folder,
                None,
            ),
            ("resume", "Reanudar partida guardada", self.resume_saved, None),
            ("history", "Historial y repetición…", self.show_history, None),
            ("export_replay", "Exportar repetición…", self.export_replay, None),
            ("open_replay", "Abrir repetición…", self.open_replay, None),
        ]
        for key, text, callback, shortcut in entries:
            if key == "history":
                menu.addSeparator()
            action = menu.addAction(_(text))
            action.triggered.connect(callback)
            if shortcut is not None:
                action.setShortcut(QKeySequence(shortcut))
            self.actions[key] = action
            self._labels[key] = text
        menu.aboutToShow.connect(self.refresh)

    def show_start(self) -> None:
        """Abre el punto de entrada común de los tres modos de juego."""
        if self.start_dialog is None:
            self.start_dialog = StartDialog(self.window)
        self.start_dialog.update_language("")
        self.start_dialog.refresh_recent()
        self.start_dialog.show()
        self.start_dialog.raise_()
        self.start_dialog.activateWindow()

    def _remember(self, path: str | Path) -> None:
        try:
            self.recent.remember(path)
        except OSError as error:
            _LOG.warning("No se pudo actualizar el índice de recientes: %s", error)

    def describe_recent(self, path: Path) -> str:
        """Identifica un autoguardado por modo, mapa y nombres públicos.

        Returns:
            Texto compacto o el nombre si el archivo no es válido.

        """
        try:
            archive = read_archive(path)
            payload = archive["payload"]
            if archive["kind"] == "replay":
                return f"{path.name} · {_('Repetición')}"
            checkpoint = payload.get("checkpoint") or payload["envelope"]["checkpoint"]
            mode = (
                _("Local")
                if "local" in payload
                else _("Por archivos")
                if "async" in payload or archive["kind"] == "turn"
                else _("LAN")
            )
            theme = _("Clásico") if checkpoint["theme"] == "classic" else _("Revancha")
            names = ", ".join(player["username"] for player in checkpoint["players"])
        except OSError, ValueError, KeyError, TypeError:
            return path.name
        else:
            return f"{mode} · {theme} · {names}\n{path.name}"

    def network_repository(self) -> FileRepository:
        """Selecciona guardados por sala y jugador para conservar votos al reiniciar.

        Returns:
            Repositorio de la sesión de red de esta ventana.

        """
        if not self.repository.session_scoped:
            self.repository = FileRepository(
                self.save_directory / f"{uuid.uuid4().hex}.pyteg", session_scoped=True
            )
        return self.repository

    def update_language(self) -> None:
        """Reaplica los textos del menú al cambiar el idioma."""
        self.menu.setTitle(_("Partida"))
        for key, label in self._labels.items():
            self.actions[key].setText(_(label))

    def refresh(self) -> None:
        """Habilita las acciones que tienen una partida o copia disponible."""
        connection = self.window.conexion
        offline = (
            isinstance(connection, OfflineConnection) and connection.game is not None
        )
        runtime = self.window.host_runtime
        available = offline or (
            runtime is not None and runtime.latest_checkpoint() is not None
        )
        self.actions["save"].setEnabled(available)
        self.actions["history"].setEnabled(available)
        self.actions["export_replay"].setEnabled(available)
        self.actions["export_turn"].setEnabled(
            isinstance(connection, OfflineConnection)
            and isinstance(connection.game, AsyncGame)
            and connection.game.can_export()
        )
        self.actions["export_folder"].setEnabled(self.last_export is not None)
        self.actions["resume"].setEnabled(
            runtime is not None and runtime.restored_waiting
        )

    def resume_saved(self) -> None:
        """Retoma el reloj de un guardado aunque falten jugadores."""
        if self.window.host_runtime is not None:
            self.window.host_runtime.resume_restored_game()

    def _error(self, error: Exception) -> None:
        QMessageBox.warning(
            self.window, _("No se pudo abrir o guardar la partida"), str(error)
        )

    def _free_for_new_session(self) -> bool:
        connection = self.window.conexion
        if connection is not None and connection.esta_ocupada():
            self._error(ValueError(_("Desconectá la partida antes de abrir otra.")))
            return False
        return True

    def _choose_save(self, title: str, suffix: str) -> str:
        path, _filter = QFileDialog.getSaveFileName(
            self.window,
            title,
            str(self.save_directory / f"partida{suffix}"),
            f"Pyteg (*{suffix})",
        )
        return path

    def save_game(self) -> None:
        """Guarda un borrador offline o la última copia de red confirmada."""
        path = self._choose_save(_("Guardar partida"), ".pyteg")
        if not path:
            return
        try:
            connection = self.window.conexion
            if (
                isinstance(connection, OfflineConnection)
                and connection.game is not None
            ):
                write_archive(path, connection.game.draft())
            elif self.window.host_runtime is not None:
                self.window.host_runtime.save_game(path)
            self.window.update_status_bar(_("Partida guardada"))
            self._remember(path)
        except (OSError, ValueError) as error:
            self._error(error)

    def open_game(self) -> bool:
        """Abre un guardado o importa la continuación de una partida por archivos.

        Returns:
            True si se abrió el archivo, False si se canceló o falló.

        """
        path, _filter = QFileDialog.getOpenFileName(
            self.window,
            _("Abrir partida o turno"),
            str(self.save_directory),
            "Pyteg (*.pyteg *.pyturn *.pyreplay)",
        )
        if not path:
            return False
        try:
            return self.open_path(path, preview=True)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self._error(error)
            return False

    def open_path(self, path: str, *, preview: bool = False) -> bool:
        """Valida el archivo antes de cambiar el mapa y la sesión.

        Returns:
            True si se abrió o ya estaba importado, False si se canceló.

        """
        archive = read_archive(path)
        if archive["kind"] == "replay":
            self._show_replay(archive["payload"])
            self._remember(path)
            return True
        connection = self.window.conexion
        continuing = False
        if (
            isinstance(connection, OfflineConnection)
            and isinstance(connection.game, AsyncGame)
            and archive["kind"] == "turn"
        ):
            if not connection.game.check_successor(archive):
                self.window.update_status_bar(_("Ese turno ya estaba abierto"))
                return True
            continuing = True
        if not continuing and not self._free_for_new_session():
            return False
        if preview and archive["kind"] == "turn":
            before = (
                self.window.client_state_model.snapshot
                if continuing and self.window.client_state_model
                else None
            )
            dialog = TurnPreviewDialog(
                TurnPreview.from_archive(archive, before), self.window
            )
            try:
                if dialog.exec() != QDialog.DialogCode.Accepted:
                    return False
            finally:
                dialog.deleteLater()
        if (
            archive["kind"] == "turn"
            or "async" in archive["payload"]
            or "local" in archive["payload"]
        ):
            self._open_offline(archive)
        else:
            self._open_network(path, archive)
        self._remember(path)
        return True

    def _open_offline(self, archive: dict[str, Any]) -> None:
        offline = OfflineConnection(self.window)
        repository = FileRepository(self.save_directory / f"{uuid.uuid4().hex}.pyteg")
        try:
            offline.open(archive, repository)
        except Exception:
            offline.deleteLater()
            raise
        connection = self.window.conexion
        if connection is not None:
            connection.desconectar()
        self.window.set_map_theme(
            offline.game.server.theme if offline.game else self.window.map_theme
        )
        self.window.reset_session_state()
        offline.conectar()
        self.repository = repository
        self._remember(repository.path)

    def _open_network(self, path: str, archive: dict[str, Any]) -> None:
        runtime = HostRuntime(repository=self.network_repository())
        try:
            port, user_id, token = runtime.restore_game(path)
            checkpoint = archive["payload"]["envelope"]["checkpoint"]
            self.window.set_map_theme(checkpoint["theme"])
        except Exception:
            runtime.close()
            raise
        self.window.reset_session_state()
        if self.window.host_runtime is not None:
            self.window.host_runtime.close()
        self.window.host_runtime = runtime
        self.window.client.set_userid(user_id)
        self.window.client.set_reconnect_token(token)
        network = ConnectionClient(self.window, "127.0.0.1", port)
        self.window.conexion = network
        self.window.transmisor = ClientTransmisor(network)
        network.conectar()

    def start_offline(
        self,
        theme: str,
        profile: str,
        players: str | list[str],
        bots: int = 0,
        *,
        difficulty: str = DEFAULT_BOT_DIFFICULTY,
    ) -> None:
        """Crea un lobby local o por archivos con mapa y perfil independientes.

        Raises:
            ValueError: Si hay otra partida activa.

        """
        connection = self.window.conexion
        if connection is not None and connection.esta_ocupada():
            msg = _("Desconectá la partida antes de abrir otra.")
            raise ValueError(msg)
        repository = FileRepository(self.save_directory / f"{uuid.uuid4().hex}.pyteg")
        offline = OfflineConnection(self.window)
        try:
            if isinstance(players, str):
                offline.create_local(
                    theme,
                    players,
                    bots,
                    repository,
                    rules_profile=profile,
                    difficulty=difficulty,
                )
            else:
                offline.create(theme, players, repository, rules_profile=profile)
            self.window.set_map_theme(theme)
            self.window.reset_session_state()
            offline.conectar()
        except Exception:
            offline.desconectar()
            offline.deleteLater()
            raise
        self.repository = repository
        self._remember(repository.path)

    def create_async(self) -> None:
        """Crea jugadores locales y deja configurar todas las reglas existentes."""
        if not self._free_for_new_session():
            return
        dialog = AsyncSetupDialog(self.window.map_theme, self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            theme = str(dialog.theme_selector.currentData())
            repository = FileRepository(
                self.save_directory / f"{uuid.uuid4().hex}.pyteg"
            )
            offline = OfflineConnection(self.window)
            offline.create(theme, dialog.names.text().split(","), repository)
            self.window.set_map_theme(theme)
            self.window.reset_session_state()
            offline.conectar()
            self.repository = repository
        except (OSError, ValueError) as error:
            self._error(error)

    def export_turn(self) -> None:
        """Guarda el turno sellado para compartirlo por cualquier medio."""
        connection = self.window.conexion
        if not isinstance(connection, OfflineConnection) or not isinstance(
            connection.game, AsyncGame
        ):
            return
        try:
            path = self._choose_save(_("Exportar turno"), ".pyturn")
            if path:
                archive = connection.game.export_turn()
                write_archive(path, archive)
                self.window.update_status_bar(_("Turno exportado para compartir"))
                self._exported(path)
        except (OSError, ValueError) as error:
            self._error(error)

    def _exported(self, path: str) -> None:
        self.last_export = Path(path).resolve()
        self._remember(path)
        if self.export_dialog is not None:
            self.export_dialog.close()
            self.export_dialog.deleteLater()
        self.export_dialog = ExportedFileDialog(self.last_export, self.window)
        self.export_dialog.show()

    def open_export_folder(self) -> None:
        """Abre la carpeta del último turno o repetición exportados."""
        if self.last_export is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_export.parent)))

    def _history(self) -> dict[str, Any]:
        connection = self.window.conexion
        if isinstance(connection, OfflineConnection) and connection.game is not None:
            return cast(
                "dict[str, Any]",
                connection.game.server.serialized(
                    connection.game.server.history.export
                ),
            )
        runtime = self.window.host_runtime
        envelope = runtime.latest_checkpoint() if runtime is not None else None
        if envelope is None:
            msg = _("Todavía no hay historial de partida")
            raise ValueError(msg)
        return cast("dict[str, Any]", envelope["checkpoint"]["history"])

    def show_history(self) -> None:
        """Abre una vista independiente que no puede enviar acciones."""
        try:
            self._show_replay(self._history())
        except ValueError as error:
            self._error(error)

    def _show_replay(self, history: dict[str, Any]) -> None:
        replay = Replay(history)
        if replay.count:
            dialog = ReplayWindow(replay, self.window)
            dialog.show()

    def export_replay(self) -> None:
        """Exporta únicamente el historial público de la partida."""
        path = self._choose_save(_("Exportar repetición"), ".pyreplay")
        if path:
            try:
                write_archive(path, make_archive("replay", self._history()))
                self._exported(path)
            except (OSError, ValueError) as error:
                self._error(error)

    def open_replay(self) -> None:
        """Abre una repetición pública, incluso durante una partida activa."""
        path, _filter = QFileDialog.getOpenFileName(
            self.window,
            _("Abrir repetición"),
            str(self.save_directory),
            "Pyteg (*.pyreplay)",
        )
        if path:
            try:
                self.open_path(path)
            except (OSError, ValueError) as error:
                self._error(error)
