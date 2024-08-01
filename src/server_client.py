import json

from src.server_player import Player
from src.server_tasks import ServerTask
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

        if soy_admin:
            self.transmisor.sos_admin()

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
        task = ServerTask.msg_to_task(data)
        task.run(self)

        mensaje = data["mensaje"]
        print(mensaje)
