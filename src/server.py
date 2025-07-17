import argparse
import sys

from src.build_mapa import build_mapa
from src.server_color import ServerColor
from src.server_estado import Estado
from src.server_game import Game
from src.server_mapa import Mapa
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
        # Notificar a todos los clientes restantes sobre la desconexión
        self.enviar_username()

    def registrar_cliente(self, user_id, client):
        self.color.asignar_color_aleatorio(client)
        self._clients[user_id] = client

    def dame_lista_jugadores(self):
        return list(self._clients.keys())

    def dame_clientes(self):
        return list(self._clients.values())

    def enviar_colores_asignados(self):
        # Obtener la lista de clientes en el orden de los turnos
        # si el juego ha comenzado
        if hasattr(self, "game") and self.game is not None:
            # Usar el orden de los turnos del juego
            clientes_ordenados = self.game.lista_jugadores_orden_turno()
            # Asegurarse de que todos los clientes estén incluidos,
            # incluso si no están en los turnos
            clientes_restantes = [
                c for c in self.dame_clientes() if c not in clientes_ordenados
            ]
            clientes_ordenados.extend(clientes_restantes)
        else:
            # Si no hay juego, usar el orden original
            clientes_ordenados = self.dame_clientes()

        # Enviar los colores asignados a todos los clientes
        for client in self.dame_clientes():
            for otro_client in clientes_ordenados:
                client.transmisor.color_asignado(
                    otro_client.userid(), otro_client.color_actual()
                )

        # Actualizar la lista de jugadores en la interfaz de usuario
        if hasattr(self, "game") and self.game is not None:
            self.actualizar_lista_jugadores_ui()

    def actualizar_lista_jugadores_ui(self):
        """
        Actualiza la lista de jugadores en la interfaz de usuario de todos los clientes.
        """
        if not hasattr(self, "game") or self.game is None:
            return

        # Obtener la lista de jugadores en el orden de los turnos
        jugadores_ordenados = self.game.lista_jugadores_orden_turno()

        # Enviar la lista actualizada a todos los clientes
        for client in self.dame_clientes():
            # Crear una lista de tuplas (userid, color) en el orden correcto
            jugadores_con_colores = [
                (jugador.userid(), jugador.color_actual())
                for jugador in jugadores_ordenados
                if hasattr(jugador, "userid") and hasattr(jugador, "color_actual")
            ]

            # Enviar la lista de jugadores al cliente
            client.transmisor.actualizar_lista_jugadores(jugadores_con_colores)

    def enviar_estado(self):
        for client in self.dame_clientes():
            client.transmisor.enviar_estado(self.estado.estado_actual())

    def enviar_turno_actual(self):
        """Envía el número de turno y ronda actuales a todos los clientes."""
        if not self.game:
            return

        turno_actual = self.game.id_turno_actual()
        # Calcular el número de ronda: (turno_actual // cant_jugadores) + 1

        # Obtener información del jugador actual
        jugador_actual_id = None
        jugador_actual_nombre = None
        jugador_actual_color = None

        try:
            turno_obj = self.game.turno_actual()
            if turno_obj and hasattr(turno_obj, "jugador_actual"):
                jugador = turno_obj.jugador_actual()

                if jugador:
                    jugador_actual_id = jugador.userid()
                    jugador_actual_nombre = jugador.username()
                    color_obj = jugador.color_actual()
                    jugador_actual_color = color_obj.to_hex() if color_obj else None

        except Exception as e:
            print(f"Error obteniendo información del jugador actual: {e}")

        for client in self.dame_clientes():
            client.transmisor.enviar_turno(
                turno_actual,
                self.game.num_ronda(),
                jugador_actual_id,
                jugador_actual_nombre,
                jugador_actual_color,
            )

        # Enviar las unidades disponibles al jugador del turno actual
        self.enviar_unidades_disponibles()

        # Enviar el mapa actualizado para actualizar las unidades disponibles
        self.enviar_mapa()

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

        # Crear e iniciar el juego, pasando la referencia al servidor
        self.game = Game(self.mapa, self.mazo, jugadores, self)
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

        # Enviar el número de turno inicial a todos los clientes
        print("Enviando número de turno inicial a los clientes...")
        self.enviar_turno_actual()

        # Iniciar el temporizador de turnos
        print("Iniciando temporizador de turnos...")
        self._turno_timer = TurnoTimer(self, segundos_por_turno=20)
        self._turno_timer.start()

    def enviar_unidades_disponibles(self):
        """Envía las unidades disponibles al jugador del turno actual."""
        if not self.game:
            return

        turno_actual = self.game.turno_actual()
        if not turno_actual:
            return

        jugador_actual = turno_actual.jugador_actual()

        # Crear diccionario con las unidades disponibles
        unidades = {"infanteria": turno_actual.cant_unidades()}

        # Agregar unidades de continentes si existen
        if (
            hasattr(turno_actual, "cant_unidades_africa")
            and turno_actual.cant_unidades_africa() > 0
        ):
            unidades["Africa"] = turno_actual.cant_unidades_africa()
        if (
            hasattr(turno_actual, "cant_unidades_europa")
            and turno_actual.cant_unidades_europa() > 0
        ):
            unidades["Europa"] = turno_actual.cant_unidades_europa()
        if (
            hasattr(turno_actual, "cant_unidades_asia")
            and turno_actual.cant_unidades_asia() > 0
        ):
            unidades["Asia"] = turno_actual.cant_unidades_asia()
        if (
            hasattr(turno_actual, "cant_unidades_sudamerica")
            and turno_actual.cant_unidades_sudamerica() > 0
        ):
            unidades["América del Sur"] = turno_actual.cant_unidades_sudamerica()
        if (
            hasattr(turno_actual, "cant_unidades_norteamerica")
            and turno_actual.cant_unidades_norteamerica() > 0
        ):
            unidades["América del Norte"] = turno_actual.cant_unidades_norteamerica()
        if (
            hasattr(turno_actual, "cant_unidades_oceania")
            and turno_actual.cant_unidades_oceania() > 0
        ):
            unidades["Oceanía"] = turno_actual.cant_unidades_oceania()

        # Enviar solo al jugador del turno actual
        for client in self.dame_clientes():
            if client.userid() == jugador_actual.userid():
                client.transmisor.enviar_unidades_disponibles(unidades)
                break

    def enviar_mapa(self):
        """Envía el estado actual del mapa a todos los clientes conectados."""
        for client in self.dame_clientes():
            client.transmisor.enviar_mapa(self.mapa, self.game)


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
