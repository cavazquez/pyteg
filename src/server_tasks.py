class ServerTaskChat:

    def __init__(self, msg):
        self._msg = msg

    def run(self, server_transmisor):
        server_transmisor.enviar_chat_a_todos(self._msg)


class ServerTask:

    @staticmethod
    def msg_to_task(data):

        if data["mensaje"] == "chat":
            msg = data["msg"]
            return ServerTaskChat(msg)

        return None
