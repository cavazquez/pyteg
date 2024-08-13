from src.server_color import ServerColor
from src.server_registrar_jugadores import registrar_jugadores


class Server:
    def __init__(self):
        self._clients = {}
        self.color = ServerColor()

    def cant_clients(self):
        return len(self._clients)

    def quitarme(self, user_id):
        print(f"Quitando {user_id}")
        self._clients.pop(user_id)

    def registrar_cliente(self, user_id, client):
        self.color.asignar_color(client)
        self._clients[user_id] = client

    def dame_lista_jugadores(self):
        return list(self._clients.keys())

    def dame_clientes(self):
        return self._clients.values()


def main():
    server = Server()
    registrar_jugadores(server)


if __name__ == "__main__":
    main()
