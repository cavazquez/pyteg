import json

from src.exception import MensajeNoValidoError
from src.server_tasks_manager import ServerTaskManager
from src.server_transmisor import ServerTransmisor


class Client:
    def __init__(self, user_id, conn, server, username, soy_admin):
        self._username = username
        self.server = server
        self._conn = conn
        self.transmisor = ServerTransmisor(self._conn)
        self._user_id = user_id
        self._soy_admin = soy_admin
        self._color = None

    def asignar_color(self, color):
        self._color = color

    def soy_admin(self):
        return self._soy_admin

    def enviar_username_a_todos(self):
        clientes = self.server.dame_clientes()
        for c in clientes:
            for otro_cliente in clientes:
                c.transmisor.enviar_username(
                    otro_cliente.userid(), otro_cliente.username()
                )

    def enviar_userid_a_todos(self):
        clientes = self.server.dame_clientes()
        for c in clientes:
            for otro_cliente in clientes:
                c.transmisor.enviar_userid(otro_cliente.userid())

    def cambiar_color(self, color):
        self.server.color.asignar_color(self, color)

    def color_actual(self):
        return self._color

    def userid(self):
        return self._user_id

    def username(self):
        return self._username

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def run(self):
        vivo = True

        self.enviar_userid_a_todos(self._user_id)
        self.enviar_username_a_todos(self._user_id, self.username)

        if self.soy_admin():
            self.transmisor.sos_admin()

        self.transmisor.enviar_colores(self.server.color.colores())
        self.transmisor.enviar_estado(self.server.estado.estado_actual())

        while vivo:
            data = self.receiver()

            if not data:
                vivo = False
                continue

            data_json = json.loads(data)
            self.ejecutar_mensaje(data_json)

    def ejecutar_mensaje(self, data):
        task = ServerTaskManager.msg_to_task(data)
        try:
            task.run(self)
        except MensajeNoValidoError as e:
            print(f"{e}")

        mensaje = data["mensaje"]
        print(mensaje)
