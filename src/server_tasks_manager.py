from typing import Any

from src.server_tasks import IServerTask, ServerTaskNull, dict_task


class ServerTaskManager:
    @staticmethod
    def msg_to_task(data: dict[str, Any]) -> IServerTask:
        mensaje = data.get("mensaje")
        if isinstance(mensaje, str):
            task_factory = dict_task.get(mensaje, ServerTaskNull)
        else:
            task_factory = ServerTaskNull
        return task_factory(data)
