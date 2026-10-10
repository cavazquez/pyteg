"""Proyección Qt del modo entre pares, con todo el TCP fuera del hilo gráfico."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from pyteg.client.hosting import local_game_addresses
from pyteg.client.offline import OfflineConnection
from pyteg.exceptions import ImagenNoEncontradaError
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.network.discovery import RoomAnnouncer

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.gui.main_window import Gui
    from pyteg.network.peer_runtime import PeerNode
from pyteg.toml_reader import TomlReaderError

_LOG = get_logger(__name__)


class PeerConnection(OfflineConnection):
    """Mantiene la interfaz existente sobre un acuerdo entre motores locales."""

    ready = Signal(object)
    changed = Signal()
    failed = Signal(str)
    completed = Signal()

    def __init__(self, window: Gui) -> None:
        """Prepara señales y una cola de comandos sin bloquear Qt."""
        super().__init__(window)
        self.node: PeerNode | None = None
        self._connecting = False
        self._busy = 0
        self._announcer: RoomAnnouncer | None = None
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="peer-ui")
        self.ready.connect(self._attach)
        self.changed.connect(self._update_availability)
        self.failed.connect(self._error)
        self.completed.connect(self._finish_command)

    def start(self, factory: Callable[[], PeerNode]) -> None:
        """Crea o recupera la sesión en segundo plano."""
        self._active = self._connecting = True
        self.window.conexion = self
        self.window.network_status_label.setText(_("Conectando entre pares…"))
        self.window.refresh_gameplay_actions()

        self.window.update_invitation_button()

        def build() -> None:
            try:
                node = factory()
            except (OSError, ValueError, KeyError, TypeError) as error:
                self._emit_failure(str(error))
                return
            if self._active:
                try:
                    self.ready.emit(node)
                except RuntimeError:
                    # La ventana pudo eliminar su QObject durante la conexión.
                    node.close()
            else:
                node.close()

        self._worker.submit(build)

    def _attach(self, node: PeerNode) -> None:
        if not self._active:
            threading.Thread(target=node.close, daemon=True).start()
            return
        self._active = self._connecting = False
        try:
            self.window.set_map_theme(node.game.server.theme)
        except (OSError, ValueError, TomlReaderError, ImagenNoEncontradaError) as error:
            threading.Thread(target=node.close, daemon=True).start()
            self.desconectar()
            self.window.update_status_bar(str(error))
            return
        self._active = True
        self.node, self.game = node, node.game
        node.set_callbacks(self._receive, self.changed.emit)
        # La base configura transmisor, identidad y proyección. El nodo envía
        # luego su snapshot privado desde el motor que esté confirmado.
        super().conectar()
        node.sync_local()
        try:
            self._announcer = RoomAnnouncer(node.describe)
            self._announcer.start()
        except OSError as error:
            _LOG.debug("No se pudo anunciar la sala entre pares: %s", error)
        self._update_availability()

    def _error(self, message: str) -> None:
        if not self._active:
            return
        if self._connecting:
            self.desconectar()
        self.window.update_status_bar(_("Error entre pares: {}").format(message))

    def _emit_failure(self, message: str) -> None:
        if self._active:
            with suppress(RuntimeError):
                # El widget puede cerrarse antes de terminar el trabajo en red.
                self.failed.emit(message)

    def send_data(self, data: str) -> None:
        """Encola acciones; sus eventos llegan únicamente después del acuerdo."""
        node = self.node
        if node is None or not self._active:
            return
        self._busy += 1
        self._update_availability()

        def apply() -> None:
            try:
                node.submit(json.loads(data))
            except (OSError, ValueError, KeyError, TypeError) as error:
                self._emit_failure(str(error))
            finally:
                if self._active:
                    with suppress(RuntimeError):
                        self.completed.emit()

        self._worker.submit(apply)

    def _finish_command(self) -> None:
        self._busy = max(0, self._busy - 1)
        self._update_availability()

    def _update_availability(self) -> None:
        node = self.node
        if not self._active or not self.window.vivo() or node is None:
            return
        self.game = node.game
        available = node.available()
        self.hosting.paused = not available or self._busy > 0
        self.window.network_status_label.setText(
            _("Entre pares · conectado")
            if available
            else _("Entre pares · esperando una mayoría")
        )
        participants = len(node.document["state"]["members"])
        addresses = ", ".join(f"{host}:{node.port}" for host in local_game_addresses())
        self.window.network_status_label.setToolTip(
            _("Tu conexión: {}").format(addresses)
            + "\n"
            + _("Se necesitan {} de {} participantes.").format(
                participants // 2 + 1, participants
            )
        )
        self.window.refresh_gameplay_actions()
        self.window.update_invitation_button()

    def esta_ocupada(self) -> bool:
        """Incluye la creación o sincronización pendiente de la sesión.

        Returns:
            True mientras se conecta o juega.

        """
        return self._active or self._connecting

    def desconectar(self) -> None:
        """Cierra la proyección y libera los recursos de red en segundo plano."""
        self._connecting = False
        if self._announcer is not None:
            self._announcer.close()
            self._announcer = None
        node, self.node = self.node, None
        self.game = None
        super().desconectar()
        if node is not None:
            node.set_callbacks(lambda _uid, _msg: None, lambda: None)
            threading.Thread(target=node.close, name="peer-close", daemon=True).start()
        self._worker.shutdown(wait=False, cancel_futures=True)
        self.window.update_invitation_button()
