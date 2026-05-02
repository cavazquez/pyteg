"""Tarea del cliente: convertir al cliente en administrador."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.types import BaseClientTaskData

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskSerAdmin(IClientTask[BaseClientTaskData]):
    """Tarea para convertir al cliente en administrador."""

    def __init__(self, data: BaseClientTaskData) -> None:
        """Inicializa la tarea de administrador.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        super().__init__(data)

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea convirtiendo al cliente en administrador."""
        main_window.client.ahora_es_admin()
        main_window.ventana_admin()
