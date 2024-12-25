from src.build_mapa import build_mapa
from src.game import Game
from src.mapa import Mapa
from src.server_color import ServerColor
from src.server_estado import Estado
from src.server_registrar_jugadores import registrar_jugadores


class Server:
    """Tiene la responsabilidad de todo lo relacionado
    con los clientes y sus conexiones"""

    def __init__(self):
        self._clients = {}
        self.color = ServerColor()
        self.estado = Estado()
        self.game = None
        self.mapa = Mapa(build_mapa)
        self.mazo = None

    def cant_clients(self):
        return len(self._clients)

    def quitarme(self, user_id):
        print(f"Quitando {user_id}")
        self._clients.pop(user_id, None)

    def registrar_cliente(self, user_id, client):
        self.color.asignar_color_aleatorio(client)
        self._clients[user_id] = client

    def dame_lista_jugadores(self):
        return list(self._clients.keys())

    def dame_clientes(self):
        return list(self._clients.values())

    def enviar_colores_asignados(self):
        for client in self.dame_clientes():
            for otro_client in self.dame_clientes():
                client.transmisor.color_asignado(
                    otro_client.userid(), otro_client.color_actual()
                )

    def enviar_estado(self):
        for client in self.dame_clientes():
            client.transmisor.enviar_estado(self.estado.estado_actual())

    def enviar_chat(self, username, msg):
        for client in self.dame_clientes():
            client.transmisor.enviar_chat(f"{username}: {msg}")

    def enviar_userid(self):
        for client in self.dame_clientes():
            for otro_client in self.dame_clientes():
                client.transmisor.enviar_userid(otro_client.userid())

    def enviar_username(self):
        for client in self.dame_clientes():
            for otro_client in self.dame_clientes():
                client.transmisor.enviar_username(
                    otro_client.userid(), otro_client.username()
                )

    def empezar_partida(self):
        jugadores = self.dame_clientes()
        self.game = Game(self.mapa, self.mazo, jugadores)
        self.game.empezar()
        self.enviar_mapa()

    def enviar_mapa(self):
        for client in self.dame_clientes():
            for pais in self.mapa.paises():
                unidades = self.mapa.cantidad_unidades(pais)
                userid = self.mapa.ocupado_por(pais).userid()
                print(f"{pais} {userid} {unidades}")
                client.transmisor.enviar_pais(pais, userid, unidades)


def main():
    server = Server()
    registrar_jugadores(server)


if __name__ == "__main__":
    main()
