from __future__ import annotations

from typing import Any

from src.client_tasks import ClientTaskNull, IClientTask, dict_task


class ClientTaskManager:
    @staticmethod
    def msg_to_task(data: dict[str, Any]) -> IClientTask:
        mensaje_raw = data.get("mensaje")
        if not isinstance(mensaje_raw, str):
            return ClientTaskNull(data)
        task_cls: type[IClientTask] = dict_task.get(mensaje_raw, ClientTaskNull)
        return task_cls(data)
