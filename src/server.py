import argparse
import sys

from src.build_mapa import build_mapa
from src.game import Game
from src.mapa import Mapa
from src.server_color import ServerColor
from src.server_estado import Estado
from src.server_registrar_jugadores import registrar_jugadores
from src.turno_timer import TurnoTimer


class Server:
    """Tiene la responsabilidad de todo lo relacionado
    con los clientes y sus conexiones"""

    def __init__(self):
        self._clients = {}
        self.color = ServerColor()
        self.estado = Estado()
        self.game = None

        # Inicializar el mapa
        self.mapa = Mapa(build_mapa)

        # Timer de turnos (se inicializa en None y se arranca al empezar la partida)
        self._turno_timer = None
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
        """
        Inicia la partida,
        asigna colores a los jugadores y notifica a todos los clientes.
        """
        print("Iniciando partida...")

        # Obtener la lista de jugadores
        jugadores = self.dame_clientes()
        print(f"Jugadores conectados: {[j.userid() for j in jugadores]}")

        # Crear e iniciar el juego
        self.game = Game(self.mapa, self.mazo, jugadores)
        self.game.empezar()

        # Enviar información de los jugadores y sus colores a todos los clientes
        print("Enviando colores asignados a los jugadores...")
        self.enviar_colores_asignados()

        # Enviar el mapa con los países y sus propietarios
        print("Enviando mapa a los jugadores...")
        self.enviar_mapa()

        # Notificar a los clientes que la partida ha comenzado
        print("Notificando a los clientes que la partida ha comenzado...")
        # Cambiar el estado a EmpezarPartida
        self.estado.empezar_partida()
        self.enviar_estado()

        print("Partida iniciada correctamente")

        # ------------------------------------------------------------------
        # Arrancar temporizador de turnos
        # ------------------------------------------------------------------
        if self._turno_timer is None:
            self._turno_timer = TurnoTimer(self)
            self._turno_timer.start()

    def enviar_mapa(self):
        # Primero, enviar la información del mapa a todos los clientes
        for client in self.dame_clientes():
            for pais in self.mapa.paises():
                unidades = self.mapa.cantidad_unidades(pais)
                userid = self.mapa.ocupado_por(pais).userid()
                print(f"{pais} {userid} {unidades}")
                client.transmisor.enviar_pais(pais, userid, unidades)

        # Luego, enviar las unidades disponibles a cada jugador
        if (
            hasattr(self, "game")
            and self.game is not None
            and hasattr(self.game, "turno_actual")
        ):
            for client in self.dame_clientes():
                # Buscar el turno del jugador actual
                turno_jugador = None
                for turno in self.game.turnos():
                    if (
                        hasattr(turno, "jugador_actual")
                        and turno.jugador_actual() == client
                    ):
                        turno_jugador = turno
                        break

                if turno_jugador is not None:
                    # Calcular unidades disponibles para este jugador
                    unidades_disponibles = {
                        "infanteria": turno_jugador.cant_unidades(),
                        "misiles": 0,  # Por defecto 0 misiles
                    }

                    # Verificar si el jugador tiene misiles disponibles (si corresponde)
                    if hasattr(turno_jugador, "cant_misiles"):
                        unidades_disponibles["misiles"] = turno_jugador.cant_misiles()

                    # Enviar las unidades disponibles al cliente
                    client.transmisor.enviar_unidades_disponibles(unidades_disponibles)


def parse_arguments() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.

    Returns:
        argparse.Namespace: Objeto con los argumentos parseados
    """
    parser = argparse.ArgumentParser(description="Servidor del juego de estrategia.")

    # Argumentos de conexión
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Dirección IP donde escuchar las conexiones (predeterminado: 127.0.0.1)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=65432,
        help="Puerto donde escuchar las conexiones (predeterminado: 65432)",
    )

    # Argumento para modo verboso
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Habilita mensajes de depuración"
    )

    return parser.parse_args()


def main():
    """
    Función principal del servidor.
    """
    args = parse_arguments()

    print(f"Iniciando servidor en {args.host}:{args.port}")
    if args.verbose:
        print("Modo verboso activado")

    try:
        server = Server()
        registrar_jugadores(server, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
