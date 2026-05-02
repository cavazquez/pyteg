"""Módulo para gestionar las tareas del cliente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.client.tasks import ClientTaskNull, IClientTask, dict_task

if TYPE_CHECKING:
    from pyteg.client.tasks.types import BaseClientTaskData


class ClientTaskManager:
    """Gestiona la conversión de mensajes a tareas del cliente."""

    @staticmethod
    def msg_to_task(data: dict[str, Any]) -> IClientTask[Any]:
        """Convierte un mensaje recibido en una tarea del cliente.

        Args:
            data: Diccionario con el mensaje y datos asociados.

        Returns:
            Instancia de `IClientTask` correspondiente al mensaje.

        """
        mensaje_raw = data.get("mensaje")
        if not isinstance(mensaje_raw, str):
            return ClientTaskNull(cast("BaseClientTaskData", data))
        task_cls: type[IClientTask[Any]] = dict_task.get(mensaje_raw, ClientTaskNull)
        return task_cls(cast("BaseClientTaskData", data))
