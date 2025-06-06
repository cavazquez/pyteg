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
        main_window.client.ahora_es_admin()
        main_window.ventana_admin()


class ClientTaskEstado(IClientTask):
    def __init__(self, data):
        self._msg = data.get("estado")

    def run(self, main_window):
        if self._msg == "EsperarJugadores":
            main_window.ventana_esperar_jugadores()
        elif self._msg == "JUGANDO":
            # Cerrar la ventana de espera si está abierta
            if hasattr(main_window, "w") and main_window.w:
                main_window.w.close()
            # Actualizar la lista de jugadores en la interfaz principal
            self.actualizar_lista_jugadores(main_window)

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        # Obtener la lista de jugadores con sus colores
        jugadores = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client:
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskColorAsignado(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        # Extraer el ID de usuario y el color del mensaje
        id_user = self._msg.pop("id")
        self._msg.pop("mensaje")

        # Asignar el color al usuario
        color = Color(**self._msg)
        main_window.colores.asignar(id_user, color)

        # Actualizar la lista de jugadores en la interfaz
        self.actualizar_lista_jugadores(main_window)

        # Actualizar la ventana de espera de jugadores si está abierta
        if main_window.w.__class__.__name__ == "VentanaEsperarJugadores":
            main_window.w.cargar_colores_asignados()

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        # Obtener la lista de jugadores con sus colores
        jugadores = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client:
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


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

        # Actualizar el nombre de usuario
        # en el cliente principal si es el propio cliente
        if main_window.client.userid() == userid:
            main_window.client.set_username(username)

        # Actualizar el nombre de usuario en el diccionario de clientes
        if userid in main_window.client_by_id:
            main_window.client_by_id[userid].set_username(username)

        # Actualizar la lista de jugadores en la interfaz
        self.actualizar_lista_jugadores(main_window)

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        # Obtener la lista de jugadores con sus colores
        jugadores = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client and client.username():
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskAsignarPais(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        pais = self._msg.get("pais")
        userid = self._msg.get("userid")
        unidades = self._msg.get("unidades")
        pais = main_window.scene.paises.get(pais)
        pais.set_unidades(unidades)
        color = main_window.colores.color_asignado(userid)
        pais.set_color(color)


dict_task = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
    "estado": ClientTaskEstado,
    "color_asignado": ClientTaskColorAsignado,
    "color": ClientTaskColor,
    "user_id": ClientTaskUserId,
    "username": ClientTaskUsername,
    "pais": ClientTaskAsignarPais,
}
