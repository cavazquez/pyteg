from abc import ABC, abstractmethod

from src.exception import MensajeNoValidoError


class IServerTask(ABC):
    @abstractmethod
    def __init__(self, data):
        self._data = data

    @abstractmethod
    def run(self, client):
        pass


class ServerTaskNull(IServerTask):
    def __init__(self, data):
        super().__init__(data)

    def run(self, _):
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)


class ServerTaskChat(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._msg = data.get("msg")

    def run(self, client):
        client.server.enviar_chat(client.username, self._msg)


class ServerTaskEmpezar(IServerTask):
    def __init__(self, data):
        super().__init__(data)

    def run(self, client):
        client.server.estado.esperar_jugadores()
        client.server.enviar_estado()


class ServerTaskSeleccionarColor(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._color = data.get("color")

    def run(self, client):
        client.cambiar_color(self._color)
        client.server.enviar_colores_asignados()


class ServerTaskEmpezarPartida(IServerTask):
    def __init__(self, data):
        super().__init__(data)

    def run(self, client):
        client.server.estado.empezar_partida()
        client.server.enviar_estado()
        client.server.empezar_partida()


dict_task = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "seleccionar_color": ServerTaskSeleccionarColor,
    "empezar_partida": ServerTaskEmpezarPartida,
}
