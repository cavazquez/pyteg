from abc import ABC, abstractmethod


class IServerTask(ABC):

    @abstractmethod
    def __init__(self, data):
        pass

    @abstractmethod
    def run(self, client):
        pass


class ServerTaskChat(IServerTask):

    def __init__(self, data):
        self._msg = data.get("msg")

    def run(self, client):
        clientes = client.server.dame_clientes()
        username = client.username
        for c in clientes:
            c.transmisor.enviar_chat(f"{username}: {self._msg}")


class ServerTaskNull(IServerTask):

    def __init__(self, data):
        pass

    def run(self, client):
        pass


dict_task = {
    "chat": ServerTaskChat,
}
