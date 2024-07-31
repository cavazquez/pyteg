from itertools import cycle

from src.server_client import Client


class ServerBuildClient:

    def __init__(self):
        self._user_id = 1
        self._username = cycle(["Cortazar", "Borges", "Sabato", "Arlt", "Bioy", "Saer"])

    def build(self, connection, server):
        username = next(self._username)
        user_id = self._user_id
        self._user_id += 1
        client = Client(user_id, connection, server, username)
        return user_id, client
