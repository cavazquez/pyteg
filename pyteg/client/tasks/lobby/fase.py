"""Tarea cliente para la fase de turno enviada por el servidor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.types import FaseTaskData

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskFase(IClientTask[FaseTaskData]):
    """Actualiza el estado de fase que consume la GUI."""

    def __init__(self, data: FaseTaskData) -> None:
        """Inicializa la tarea con la fase recibida."""
        super().__init__(data)

    def run(self, main_window: GameWindowProtocol) -> None:
        """Actualiza la fase que consume la interfaz."""
        fase = self._raw_data.get("fase", "acciones")
        main_window.fase_actual = fase
        main_window.unidades_pendientes_servidor = int(
            self._raw_data.get("unidades_pendientes", 0)
        )
        refrescar = getattr(main_window, "refresh_gameplay_actions", None)
        if callable(refrescar):
            refrescar()
