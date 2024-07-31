class ServerTaskChat:

    def __init__(self, msg):
        self._msg = msg

    def run(self, client):
        clientes = client.server.dame_clientes()
        username = client.username
        for c in clientes:
            c.transmisor.enviar_chat(f"{username}: {self._msg}")


class ServerTask:

    @staticmethod
    def msg_to_task(data):

        if data["mensaje"] == "chat":
            msg = data["msg"]
            return ServerTaskChat(msg)

        return None
