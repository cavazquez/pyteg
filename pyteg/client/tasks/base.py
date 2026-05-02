"""Tareas del cliente: interfaz base y mensajes desconocidos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class IClientTask(ABC):
    """Interfaz base para todas las tareas del cliente."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea con los datos recibidos.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        self._raw_data = data

    @abstractmethod
    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea.

        Args:
            main_window: Ventana principal de la aplicación.

        """


class ClientTaskNull(IClientTask):
    """Tarea para manejar mensajes desconocidos."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea con un mensaje desconocido.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        super().__init__(data)
        self._msg = data.get("mensaje")

    def run(self, main_window: GameWindowProtocol) -> None:  # noqa: ARG002
        """Ejecuta la tarea mostrando un mensaje de error."""
        CLIENT_TASKS_LOG.debug("Mensaje desconocido: %s", self._msg)
