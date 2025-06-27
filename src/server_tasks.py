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
        client.server.enviar_chat(client.username(), self._msg)


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


class ServerTaskSetUsername(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._username = data.get("username")

    def run(self, client):
        if self._username and isinstance(self._username, str):
            # Actualizar el nombre de usuario del cliente
            client.set_username(self._username)
            # Notificar a todos los clientes sobre el cambio de nombre
            client.server.enviar_username()
            print(
                f"Usuario {client.userid()} ha cambiado su nombre a: {self._username}"
            )


class ServerTaskAgregarUnidad(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais = data.get("pais")
        self._tipo_unidad = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica

    def run(self, client):
        # Verificar que el cliente sea el dueño del país
        if client.server.mapa.ocupado_por(self._pais) != client:
            print(f"El jugador {client.userid()} no es dueño de {self._pais}")
            return

        # Verificar que el tipo de unidad sea válido
        if self._tipo_unidad not in {"infanteria", "misil"}:
            print(f"Tipo de unidad no válido: {self._tipo_unidad}")
            return

        # Agregar la unidad al país
        for _ in range(self._cantidad):
            client.server.mapa.agregar_una_unidad(self._pais)

        msg = f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
        msg += f" en {self._pais}"
        print(msg)

        # Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()


dict_task = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "seleccionar_color": ServerTaskSeleccionarColor,
    "empezar_partida": ServerTaskEmpezarPartida,
    "set_username": ServerTaskSetUsername,
    "agregar_unidad": ServerTaskAgregarUnidad,
}
