"""Módulo para gestionar las tareas del servidor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.server.tasks import IServerTask, ServerTaskNull, dict_task

if TYPE_CHECKING:
    from pyteg.server.tasks.types import BaseTaskData


class ServerTaskManager:
    """Gestiona la conversión de mensajes a tareas del servidor."""

    @staticmethod
    def msg_to_task(data: dict[str, Any]) -> IServerTask[Any]:
        """Convierte un mensaje recibido en una tarea del servidor.

        Args:
            data: Diccionario con el mensaje y datos asociados.

        Returns:
            Instancia de `IServerTask` correspondiente al mensaje.

        """
        mensaje = data.get("mensaje")
        if isinstance(mensaje, str):
            task_factory = dict_task.get(mensaje, ServerTaskNull)
        else:
            task_factory = ServerTaskNull
        return task_factory(cast("BaseTaskData", data))
