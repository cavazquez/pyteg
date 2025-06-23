from src.server_client import Client


class ServerBuildClient:
    def __init__(self):
        self._user_id = 1
        # Ya no usamos la lista de nombres predefinidos
        # ya que el cliente proporcionará su propio nombre de usuario

    def build(self, connection, server, username=None):
        # Si no se proporciona un nombre de usuario, usar uno genérico
        if not username:
            username = f"Jugador_{self._user_id}"

        user_id = self._user_id
        self._user_id += 1
        es_admin = user_id == 1
        client = Client(user_id, connection, server, username, es_admin)
        return user_id, client
