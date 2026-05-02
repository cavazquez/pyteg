"""Módulo principal del servidor del juego."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Any

from pyteg.build_mapa import build_mapa
from pyteg.mazo import Mazo
from pyteg.objetivos_secretos import ObjetivosSecretos
from pyteg.server.conexion.broadcaster import ServerMessageBroadcaster
from pyteg.server.conexion.registrar_jugadores import registrar_jugadores
from pyteg.server.conexion.registry import ServerClientRegistry
from pyteg.server.juego.color import ServerColor
from pyteg.server.juego.coordinator import ServerGameCoordinator
from pyteg.server.juego.estado import Estado
from pyteg.server.juego.mapa import Mapa
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path
from pyteg.version import NAME, VERSION

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.game import Game


class Server:
    """Gestiona clientes y sus conexiones.

    Tiene la responsabilidad de todo lo relacionado con los clientes
    y sus conexiones.
    """

    def __init__(self) -> None:
        """Inicializa el servidor con mapa, mazo y configuración inicial."""
        self._client_registry = ServerClientRegistry()
        self.color = ServerColor()
        self.estado = Estado()
        # Inicializar broadcaster de mensajes
        self._broadcaster = ServerMessageBroadcaster(self.dame_clientes)

        # Inicializar el mapa
        self.mapa = Mapa(build_mapa)

        # Inicializar el mazo con los países del mapa y símbolos de cartas
        paises = self.mapa.paises()
        simbolos = ["Galeon", "Globo", "Canon", "Comodin"]
        self.mazo = Mazo(paises, simbolos)

        # Inicializar sistema de objetivos secretos

        # Crear TomlReader para objetivos secretos
        paises_path = get_resource_path("themes/classic/paises.toml")
        cartas_path = get_resource_path("themes/classic/cartas.toml")
        adyacencias_path = get_resource_path("themes/classic/adyacencias.toml")
        objetivos_path = get_resource_path("themes/classic/objetivos_secretos.toml")

        paises_content = paises_path.read_text(encoding="utf-8")
        cartas_content = cartas_path.read_text(encoding="utf-8")
        adyacencias_content = adyacencias_path.read_text(encoding="utf-8")
        objetivos_content = objetivos_path.read_text(encoding="utf-8")

        toml_reader = TomlReader(
            paises_content, cartas_content, adyacencias_content, objetivos_content
        )
        self.objetivos_secretos = ObjetivosSecretos(toml_reader)

        # Inicializar coordinador de partidas
        self._game_coordinator = ServerGameCoordinator(
            self.mapa,
            self.mazo,
            self.objetivos_secretos,
            self.estado,
            self.dame_clientes,
            self._broadcaster,
            self.color,
        )

    @property
    def game(self) -> Game | None:
        """Obtiene la instancia del juego actual.

        Returns:
            Instancia del juego o None si no ha comenzado.

        """
        return self._game_coordinator.game()

    def set_segundos_por_turno(self, segundos: int) -> None:
        """Configura la cantidad de segundos por turno.

        Args:
            segundos: Segundos por turno (> 0).

        """
        self._game_coordinator.set_segundos_por_turno(segundos)

    def set_paises_para_victoria(self, paises: int) -> None:
        """Configura la cantidad de países necesarios para ganar.

        Args:
            paises: Países necesarios para victoria (> 0).

        """
        self._game_coordinator.set_paises_para_victoria(paises)

    def set_objetivos_secretos(self, *, activados: bool) -> None:
        """Configura si los objetivos secretos están activados.

        Args:
            activados: True si los objetivos secretos están activados.

        """
        self._game_coordinator.set_objetivos_secretos(activados=activados)

    def set_misiles_habilitados(self, *, activados: bool) -> None:
        """Configura si los misiles están habilitados.

        Args:
            activados: True si los misiles están habilitados.

        """
        self._game_coordinator.set_misiles_habilitados(activados=activados)

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados en esta partida.

        Returns:
            True si los misiles están habilitados.

        """
        return self._game_coordinator.misiles_habilitados()

    def cant_clients(self) -> int:
        """Obtiene la cantidad de clientes conectados.

        Returns:
            Cantidad de clientes conectados.

        """
        return self._client_registry.cantidad()

    def quitarme(self, user_id: int) -> None:
        """Desconecta un cliente del servidor.

        Args:
            user_id: ID del cliente a desconectar.

        """
        print(f"Quitando {user_id}")
        self._client_registry.desconectar_cliente(user_id)
        # Notificar a todos los clientes restantes sobre la desconexión
        self.enviar_username()

    def registrar_cliente(self, user_id: int, client: Client) -> None:
        """Registra un nuevo cliente en el servidor.

        Args:
            user_id: ID único del cliente.
            client: Objeto cliente a registrar.

        """
        # Asignar color antes de registrar
        self.color.asignar_color_aleatorio(client)
        self._client_registry.registrar_cliente(user_id, client)

    def dame_lista_jugadores(self) -> list[int]:
        """Obtiene la lista de IDs de jugadores conectados.

        Returns:
            Lista de IDs de jugadores.

        """
        return self._client_registry.obtener_ids()

    def dame_clientes(self) -> list[Client]:
        """Obtiene la lista de clientes conectados.

        Returns:
            Lista de clientes.

        """
        return self._client_registry.obtener_todos()

    def enviar_colores_asignados(self) -> None:
        """Envía los colores asignados a todos los clientes.

        Los envía en el orden de los turnos.
        """
        # Obtener la lista de clientes en el orden de los turnos
        # si el juego ha comenzado
        if hasattr(self, "game") and self.game is not None:
            # Usar el orden de los turnos del juego (devuelve nombres de jugadores)
            jugadores_orden_nombres = self.game.lista_jugadores_orden_turno()
            # Convertir nombres a objetos Client
            clientes_ordenados: list[Client] = []
            for nombre in jugadores_orden_nombres:
                for client in self.dame_clientes():
                    if client.username() == nombre:
                        clientes_ordenados.append(client)
                        break
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
                color = otro_client.color_actual()
                if color is not None:
                    client.transmisor.color_asignado(otro_client.userid(), color)

        # Actualizar la lista de jugadores en la interfaz de usuario
        if hasattr(self, "game") and self.game is not None:
            self.actualizar_lista_jugadores_ui()

    def actualizar_lista_jugadores_ui(self) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista para todos los clientes.
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

    def enviar_estado(self) -> None:
        """Envía el estado actual del juego a todos los clientes."""
        self._broadcaster.enviar_estado(self.estado.estado_actual())

    def enviar_turno_actual(self) -> None:
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
                jugador_nombre = turno_obj.jugador_actual()

                if jugador_nombre:
                    # Buscar el cliente correspondiente al nombre
                    for client in self.dame_clientes():
                        if client.username() == jugador_nombre:
                            jugador_actual_id = client.userid()
                            jugador_actual_nombre = client.username()
                            color_obj = client.color_actual()
                            jugador_actual_color = (
                                color_obj.to_hex() if color_obj else None
                            )
                            break

        except (AttributeError, KeyError) as e:
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

    def enviar_chat(self, username: str, msg: str) -> None:
        """Envía un mensaje de chat a todos los clientes.

        Args:
            username: Nombre de usuario del remitente.
            msg: Mensaje de chat.

        """
        self._broadcaster.enviar_chat(username, msg)

    def enviar_userid(self) -> None:
        """Envía los IDs de usuario a todos los clientes."""
        self._broadcaster.enviar_userid()

    def enviar_username(self) -> None:
        """Envía los nombres de usuario a todos los clientes."""
        self._broadcaster.enviar_username()

    def empezar_partida(self) -> None:
        """Inicia la partida.

        Asigna colores a los jugadores y notifica a todos los clientes.
        """
        self._game_coordinator.empezar_partida(self)

    def enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador del turno actual."""
        if not self.game:
            return

        turno_actual = self.game.turno_actual()
        if not turno_actual:
            return

        jugador_actual = turno_actual.jugador_actual()

        # Delegar la construcción del dict al turno — cada clase sabe qué tiene
        unidades = turno_actual.unidades_por_tipo()

        # Enviar solo al jugador del turno actual
        for client in self.dame_clientes():
            if client.username() == jugador_actual:
                client.transmisor.enviar_unidades_disponibles(unidades)
                break

    def enviar_mapa(self) -> None:
        """Envía el estado actual del mapa a todos los clientes conectados."""
        self._broadcaster.enviar_mapa(self.mapa, self.game)

    def enviar_victoria(self, ganador_id: str, ganador_nombre: str) -> None:
        """Envía el mensaje de victoria a todos los clientes conectados."""
        self._broadcaster.enviar_victoria(ganador_id, ganador_nombre)

    def enviar_configuracion_partida(self) -> None:
        """Envía la configuración de la partida a todos los clientes conectados."""
        self._game_coordinator.enviar_configuracion_partida()

    def enviar_resultado_batalla(self, resultado_data: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes.

        Args:
            resultado_data: Datos del resultado de la batalla.

        """
        self._broadcaster.enviar_resultado_batalla(resultado_data)

    def enviar_resultado_misil(self, resultado_data: dict[str, Any]) -> None:
        """Envía el resultado del lanzamiento de un misil a todos los clientes.

        Args:
            resultado_data (dict): Datos del resultado del misil

        """
        self._broadcaster.enviar_resultado_misil(resultado_data)

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de que se agregó un misil a un país.

        Args:
            pais (str): Nombre del país donde se agregó el misil
            cantidad_misiles (int): Cantidad total de misiles en el país

        """
        self._broadcaster.enviar_misil_agregado(pais, cantidad_misiles)

    def enviar_tarjetas_jugador(self, client: Client) -> None:
        """Envía las tarjetas del jugador específico al cliente."""
        tarjetas_jugador = self.mazo.tarjetas_asignadas(client)
        tarjetas_data = [
            {"pais": tarjeta.pais, "simbolo": tarjeta.simbolo}
            for tarjeta in tarjetas_jugador
        ]
        print(
            f"Enviando {len(tarjetas_data)} tarjetas a {client.username()}: "
            f"{tarjetas_data}"
        )
        self._broadcaster.enviar_tarjetas_jugador(client, tarjetas_data)

    def enviar_objetivos_secretos(self) -> None:
        """Envía el objetivo secreto asignado a cada jugador."""
        print("=== ENVIANDO OBJETIVOS SECRETOS ===")
        self._broadcaster.enviar_objetivos_secretos(
            self.objetivos_secretos.get_objetivo_jugador
        )
        print("=== FIN ENVÍO OBJETIVOS SECRETOS ===")


def parse_arguments() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos.

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


def main() -> None:
    """Función principal del servidor."""
    args = parse_arguments()

    print(f"{NAME} v{VERSION}")
    print(f"Iniciando servidor en {args.host}:{args.port}")
    if args.verbose:
        print("Modo verboso activado")

    try:
        server = Server()
        registrar_jugadores(server, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
        sys.exit(0)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error al iniciar el servidor: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
