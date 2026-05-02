"""Tareas del cliente: interfaz base y mensajes desconocidos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.client.tasks.types import BaseClientTaskData

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol

TData = TypeVar("TData", bound=BaseClientTaskData)


class IClientTask(ABC, Generic[TData]):
    """Interfaz base para todas las tareas del cliente.

    Parametrizada por `TData` (subtipo de `BaseClientTaskData`) para que
    cada subclase declare la forma exacta del payload que recibe.
    """

    def __init__(self, data: TData) -> None:
        """Inicializa la tarea con los datos recibidos.

        Args:
            data: Diccionario con los datos de la tarea (tipados por la
                subclase).

        """
        self._raw_data: TData = data

    @abstractmethod
    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea.

        Args:
            main_window: Ventana principal de la aplicación.

        """


class ClientTaskNull(IClientTask[BaseClientTaskData]):
    """Tarea para manejar mensajes desconocidos."""

    def __init__(self, data: BaseClientTaskData) -> None:
        """Inicializa la tarea con un mensaje desconocido.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        super().__init__(data)
        self._msg = data.get("mensaje")

    def run(self, main_window: GameWindowProtocol) -> None:  # noqa: ARG002
        """Ejecuta la tarea mostrando un mensaje de error."""
        CLIENT_TASKS_LOG.debug("Mensaje desconocido: %s", self._msg)
