"""Tarea para recuperar una sesión de juego desconectada."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import ReconectarTaskData

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskReconectar(IServerTask[ReconectarTaskData]):
    """Valida y aplica una solicitud de reconexión."""

    def __init__(self, data: ReconectarTaskData) -> None:
        """Inicializa la tarea con identidad y token recibidos."""
        super().__init__(data)
        self._action_name = "reconectar"

    def _execute(
        self,
        client: IClientProtocol,
        context: GameContext,  # noqa: ARG002
    ) -> bool:
        success = client.server.reconectar_cliente(
            client,
            self._data["user_id"],
            self._data["token"],
        )
        if not success:
            client.transmisor.enviar_error(
                "reconnect_rejected",
                "El token no es válido o la sesión ya no puede reconectarse.",
            )
            return False
        return True
