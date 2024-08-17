from abc import ABC, abstractmethod

from src.client_color import Color


class IClientTask(ABC):

    @abstractmethod
    def run(self, main_window):
        pass


class ClientTaskNull(IClientTask):

    def __init__(self, data):
        self._msg = data.get("mensaje")

    def run(self, _):
        print(f"mensaje {self._msg} desconocido")


class ClientTaskChat(IClientTask):

    def __init__(self, data):
        self._msg = data.get("msg")

    def run(self, main_window):
        main_window.chat.append(self._msg)


class ClientTaskSerAdmin(IClientTask):

    def __init__(self, data):
        pass

    def run(self, main_window):
        main_window.soy_admin = True
        main_window.ventana_admin()


class ClientTaskEsperarJugadores(IClientTask):

    def __init__(self, data):
        pass

    def run(self, main_window):
        main_window.ventana_esperar_jugadores()


class ClientTaskColorAsignado(IClientTask):

    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        id_user = self._msg.pop("id")
        self._msg.pop("mensaje")
        print(f"Color asignado: {self._msg}")
        main_window.colores.asignar(id_user, Color(**self._msg))
        print(main_window.colores)


class ClientTaskColor(IClientTask):

    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        self._msg.pop("mensaje")
        print(f"Color recibido: {self._msg}")
        main_window.colores.agregar_color(Color(**self._msg))
        print(f"colores: {main_window.colores}")


dict_task = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
    "esperar_jugadores": ClientTaskEsperarJugadores,
    "color_asignado": ClientTaskColorAsignado,
    "color": ClientTaskColor,
}
