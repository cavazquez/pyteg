from src.client_tasks import ClientTaskNull, dict_task


class ClientTaskManager:
    @staticmethod
    def msg_to_task(data):
        mensaje = data.get("mensaje")
        task = dict_task.get(mensaje, ClientTaskNull)
        return task(data)
