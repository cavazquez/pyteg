from src.server_tasks import ServerTaskNull, dict_task


class ServerTaskManager:

    @staticmethod
    def msg_to_task(data):

        mensaje = data.get("mensaje")
        task = dict_task.get(mensaje, ServerTaskNull)
        return task(data)
