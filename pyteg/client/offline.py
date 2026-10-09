"""Adaptador Qt de una partida local que intercambia turnos por archivos."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from PySide6.QtCore import QObject, QTimer, Signal

from pyteg.client.conexion.transmisor import ClientNullTransmisor, ClientTransmisor
from pyteg.client.event_processor import ClientEventProcessor
from pyteg.client.state_adapter import QtClientStateAdapter
from pyteg.client.state_model import ClientStateModel
from pyteg.client.tasks.manager import ClientTaskManager
from pyteg.i18n import translate as _
from pyteg.logger import get_logger
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.protocol_validation import validate_client_event

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol
    from pyteg.gui.main_window import Gui
    from pyteg.gui.managers.protocols import MainWindowProtocol
    from pyteg.persistence.archive import ArchiveRepository


_LOG = get_logger(__name__)


class OfflineConnection(QObject):
    """Mismo transmisor y proyección Qt con un transporte en memoria."""

    received = Signal(dict)

    def __init__(self, window: Gui) -> None:
        """Prepara la proyección antes de crear o restaurar el motor."""
        super().__init__(window)
        self.window = window
        self.state_model = ClientStateModel()
        self.event_processor = ClientEventProcessor(self.state_model)
        self.state_adapter = QtClientStateAdapter(
            cast("MainWindowProtocol", window), self.state_model
        )
        self.hosting = SimpleNamespace(paused=False)
        self.game: AsyncGame | None = None
        self._active = False
        self._availability_timer = QTimer(self)
        self._availability_timer.setSingleShot(True)
        self._availability_timer.timeout.connect(self._update_availability)
        self.received.connect(self._process)

    def create(
        self, theme: str, names: list[str], repository: ArchiveRepository
    ) -> None:
        """Crea un lobby offline y conserva el trabajo automáticamente."""
        self.game = AsyncGame.create(
            theme, names, receive=self._receive, repository=repository
        )

    def open(self, archive: dict[str, Any], repository: ArchiveRepository) -> None:
        """Carga un turno validado antes de modificar la ventana."""
        self.game = AsyncGame.open(
            archive, receive=self._receive, repository=repository
        )

    def _receive(self, _user_id: int, event: dict[str, Any]) -> None:
        if self._active:
            self.received.emit(event)

    def conectar(self) -> None:
        """Proyecta la identidad local y su estado inicial."""
        game = self.game
        if game is None:
            return
        self._active = True
        self.window.conexion = self
        self.window.transmisor = ClientTransmisor(self)
        self.window.client_state_model = self.state_model
        self.window.client.set_userid(game.user_id)
        self.state_model.local_userid = game.user_id
        self.window.client.asignar_admin(enabled=False)
        self.window.network_status_label.setText(_("Partida por archivos"))
        self.window.timer_label.setText(_("Sin límite de tiempo"))
        if self.window.toolbar is not None:
            self.window.toolbar.actualizar_estado_conexion(conectado=True)
        game.sync_local()
        self._update_availability()

    def _process(self, event: dict[str, Any]) -> None:
        if not self._active or not self.window._vivo:  # noqa: SLF001 -- ciclo de vida Qt.
            return
        validated = validate_client_event(event)
        applied = self.event_processor.process(validated)
        self.state_adapter.apply(validated, applied)
        if not self.state_adapter.handles(validated["mensaje"]):
            task = ClientTaskManager.msg_to_task(validated)
            task.run(cast("GameWindowProtocol", self.window))

    def send_data(self, data: str) -> None:
        """Aplica un comando del transmisor al motor offline."""
        game = self.game
        if game is None or not self._active:
            return
        try:
            result = game.apply(json.loads(data))
        except (OSError, ValueError) as error:
            self.window.update_status_bar(str(error))
            return
        self._availability_timer.start(0)
        if (
            result
            and result.get("accepted")
            and json.loads(data).get("mensaje") == "finalizar_turno"
        ):
            self.window.update_status_bar(
                _("Turno terminado. Exportalo desde Partida → Exportar turno.")
            )

    def _update_availability(self) -> None:
        if self._active and self.window.vivo() and self.game is not None:
            self.hosting.paused = (
                self.game.handed_off or self.game.holder() != self.game.user_id
            )
            self.window.refresh_gameplay_actions()

    def esta_conectado(self) -> bool:
        """Indica si esta copia está abierta.

        Returns:
            True mientras el motor local permanece activo.

        """
        return self._active

    def esta_ocupada(self) -> bool:
        """Impide abrir otra sesión sobre una partida offline.

        Returns:
            True mientras el motor está abierto.

        """
        return self._active

    def desconectar(self) -> None:
        """Guarda el borrador y cierra la sesión local."""
        self._active = False
        self._availability_timer.stop()
        if self.game is not None:
            try:
                self.game.close()
            except (OSError, ValueError) as error:
                _LOG.warning("No se pudo guardar al cerrar la partida local: %s", error)
        if self.window.conexion is self:
            self.window.conexion = None
            self.window.transmisor = ClientNullTransmisor()
            self.window.update_game_state("Desconectado")
            self.window.network_status_label.setText(_("Desconectado"))
            if self.window.toolbar is not None:
                self.window.toolbar.actualizar_estado_conexion(conectado=False)

    def abortar(self) -> None:
        """Cierra la copia local cuando una tarea solicita abortar la sesión."""
        self.desconectar()
