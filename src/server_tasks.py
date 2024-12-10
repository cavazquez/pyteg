from abc import ABC, abstractmethod

from src.exception import MensajeNoValidoError


class IServerTask(ABC):
    @abstractmethod
    def __init__(self, data):
        pass

    @abstractmethod
    def run(self, client):
        pass


class ServerTaskNull(IServerTask):
    def __init__(self, data):
        self._data = data

    def run(self, _):
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)


class ServerTaskChat(IServerTask):
    def __init__(self, data):
        self._msg = data.get("msg")

    def run(self, client):
        clientes = client.server.dame_clientes()
        username = client.username
        for c in clientes:
            c.transmisor.enviar_chat(f"{username}: {self._msg}")


class ServerTaskEmpezar(IServerTask):
    def __init__(self, data):
        pass

    def run(self, client):
        clientes = client.server.dame_clientes()
        for c in clientes:
            c.transmisor.esperar_jugadores()


class ServerTaskSeleccionarColor(IServerTask):
    def __init__(self, data):
        self._color = data.get("color")

    def run(self, client):
        client.cambiar_color(self._color)


dict_task = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "seleccionar_color": ServerTaskSeleccionarColor,
}
