import json

from src.exception import MensajeNoValidoError
from src.server_player import Player
from src.server_tasks_manager import ServerTaskManager
from src.server_transmisor import ServerTransmisor


class Client:
    def __init__(self, user_id, conn, server, username, soy_admin):
        self.username = username
        self.server = server
        self._conn = conn
        self.transmisor = ServerTransmisor(self._conn)
        self._player = Player()
        self._user_id = user_id
        self._soy_admin = soy_admin
        self._color = None

        self.transmisor.enviar_id(self._user_id)

        if soy_admin:
            self.transmisor.sos_admin()

        self.transmisor.enviar_colores(self.server.color.colores())

    def asignar_color(self, color):
        self._color = color
        self.transmisor.color_asignado(self._user_id, color)

    def cambiar_color(self, color):
        self.server.color.asignar_color(self, color)

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def run(self):
        vivo = True

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
