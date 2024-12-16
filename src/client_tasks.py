from abc import ABC, abstractmethod

from src.client import Client
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
        main_window.colores.asignar(id_user, Color(**self._msg))
        print(f"{main_window.colores}")
        print(main_window.w.__class__.__name__)
        if main_window.w.__class__.__name__ == "VentanaEsperarJugadores":
            main_window.w.cargar_colores_asignados()


class ClientTaskColor(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        self._msg.pop("mensaje")
        main_window.colores.agregar_color(Color(**self._msg))


class ClientTaskUserId(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        userid = int(self._msg.get("user_id"))
        main_window.client.set_userid(userid)
        main_window.client_by_id[userid] = Client()
        main_window.client_by_id[userid].set_userid(userid)


class ClientTaskUsername(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        username = self._msg.get("username")
        userid = self._msg.get("user_id")
        main_window.client.set_username(username)
        main_window.client_by_id[userid].set_username(username)
        print(f"ClientTaskUsername, {userid=} , {username=}")


dict_task = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
    "esperar_jugadores": ClientTaskEsperarJugadores,
    "color_asignado": ClientTaskColorAsignado,
    "color": ClientTaskColor,
    "user_id": ClientTaskUserId,
    "username": ClientTaskUsername,
}
