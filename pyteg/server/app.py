"""Módulo principal del servidor del juego."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Any

from pyteg.core.cartas.mazo import Mazo
from pyteg.core.mapa.build_mapa import build_mapa
from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
from pyteg.log_cli import add_log_arguments
from pyteg.logger import get_logger
from pyteg.server.conexion.broadcaster import ServerMessageBroadcaster
from pyteg.server.conexion.registrar_jugadores import registrar_jugadores
from pyteg.server.conexion.registry import ServerClientRegistry
from pyteg.server.juego.color import ServerColor
from pyteg.server.juego.coordinator import ServerGameCoordinator
from pyteg.server.juego.estado import Estado
from pyteg.server.juego.mapa import Mapa
from pyteg.server.logging_setup import configure_server_logging
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path
from pyteg.version import NAME, VERSION

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.game import Game
    from pyteg.server.msg.types import BattleResultPayload, MissileResultPayload


LOGGER = get_logger(__name__)


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
        LOGGER.info("Quitando cliente %s", user_id)
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
        clientes_ordenados: list[Client]
        if hasattr(self, "game") and self.game is not None:
            jugadores_orden_ids = self.game.lista_jugadores_orden_turno()
            clientes_por_id: dict[int, Client] = {
                int(c.userid()): c for c in self.dame_clientes()
            }
            clientes_ordenados = [
                clientes_por_id[uid]
                for uid in jugadores_orden_ids
                if uid in clientes_por_id
            ]
            clientes_restantes = [
                c for c in self.dame_clientes() if c not in clientes_ordenados
            ]
            clientes_ordenados.extend(clientes_restantes)
        else:
            clientes_ordenados = self.dame_clientes()

        for client in self.dame_clientes():
            for otro_client in clientes_ordenados:
                color = otro_client.color_actual()
                if color is not None:
                    client.transmisor.color_asignado(otro_client.userid(), color)

        if hasattr(self, "game") and self.game is not None:
            self.actualizar_lista_jugadores_ui()

    def actualizar_lista_jugadores_ui(self) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista para todos los clientes.
        """
        if not hasattr(self, "game") or self.game is None:
            return

        jugadores_orden_ids = self.game.lista_jugadores_orden_turno()
        clientes_por_id: dict[int, Client] = {
            int(c.userid()): c for c in self.dame_clientes()
        }

        for client in self.dame_clientes():
            jugadores_con_colores: list[tuple[int, Any]] = []
            for uid in jugadores_orden_ids:
                cliente = clientes_por_id.get(int(uid))
                if cliente is None:
                    continue
                color = cliente.color_actual()
                jugadores_con_colores.append((cliente.userid(), color))

            client.transmisor.actualizar_lista_jugadores(jugadores_con_colores)

    def enviar_estado(self) -> None:
        """Envía el estado actual del juego a todos los clientes."""
        self._broadcaster.enviar_estado(self.estado.estado_actual())

    def enviar_turno_actual(self) -> None:
        """Envía el número de turno y ronda actuales a todos los clientes."""
        if not self.game:
            return

        turno_actual = self.game.id_turno_actual()

        jugador_actual_id: int | None = None
        jugador_actual_nombre: str | None = None
        jugador_actual_color: str | None = None

        try:
            turno_obj = self.game.turno_actual()
            if turno_obj and hasattr(turno_obj, "jugador_actual"):
                jugador_id = turno_obj.jugador_actual()

                if jugador_id:
                    cliente = self._client_registry.obtener_cliente(int(jugador_id))
                    if cliente is not None:
                        jugador_actual_id = cliente.userid()
                        jugador_actual_nombre = cliente.username()
                        color_obj = cliente.color_actual()
                        jugador_actual_color = color_obj.to_hex() if color_obj else None

        except (AttributeError, KeyError) as e:
            LOGGER.warning("Error obteniendo información del jugador actual: %s", e)

        for client in self.dame_clientes():
            client.transmisor.enviar_turno(
                turno_actual,
                self.game.num_ronda(),
                jugador_actual_id,
                jugador_actual_nombre,
                jugador_actual_color,
            )

        self.enviar_unidades_disponibles()

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

        jugador_actual_id = turno_actual.jugador_actual()
        unidades = turno_actual.unidades_por_tipo()

        cliente = self._client_registry.obtener_cliente(int(jugador_actual_id))
        if cliente is not None:
            cliente.transmisor.enviar_unidades_disponibles(unidades)

    def enviar_mapa(self) -> None:
        """Envía el estado actual del mapa a todos los clientes conectados."""
        self._broadcaster.enviar_mapa(self.mapa, self.game)

    def enviar_victoria(self, ganador_id: int, ganador_nombre: str) -> None:
        """Envía el mensaje de victoria a todos los clientes conectados."""
        self._broadcaster.enviar_victoria(ganador_id, ganador_nombre)

    def enviar_configuracion_partida(self) -> None:
        """Envía la configuración de la partida a todos los clientes conectados."""
        self._game_coordinator.enviar_configuracion_partida()

    def enviar_resultado_batalla(self, resultado_data: BattleResultPayload) -> None:
        """Envía el resultado de una batalla a todos los clientes.

        Args:
            resultado_data: Payload tipado del resultado de la batalla.

        """
        self._broadcaster.enviar_resultado_batalla(resultado_data)

    def enviar_resultado_misil(self, resultado_data: MissileResultPayload) -> None:
        """Envía el resultado del lanzamiento de un misil a todos los clientes.

        Args:
            resultado_data: Payload tipado del resultado del misil.

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
        LOGGER.debug(
            "Enviando %s tarjetas a %s: %s",
            len(tarjetas_data),
            client.username(),
            tarjetas_data,
        )
        self._broadcaster.enviar_tarjetas_jugador(client, tarjetas_data)

    def enviar_objetivos_secretos(self) -> None:
        """Envía el objetivo secreto asignado a cada jugador."""
        LOGGER.debug("Enviando objetivos secretos a los jugadores")
        self._broadcaster.enviar_objetivos_secretos(
            self.objetivos_secretos.get_objetivo_jugador,
        )
        LOGGER.debug("Objetivos secretos enviados")


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

    add_log_arguments(
        parser,
        verbose_help="Nivel DEBUG en consola (tráfico de red, batallas, mensajes)",
    )

    return parser.parse_args()


def main() -> None:
    """Función principal del servidor."""
    args = parse_arguments()
    logger = configure_server_logging(args)

    logger.info("%s v%s", NAME, VERSION)
    logger.info("Iniciando servidor en %s:%s", args.host, args.port)
    if args.verbose:
        logger.debug("Modo verboso: tráfico de red y detalle de batallas en consola")
    elif args.quiet:
        logger.debug("Modo silencioso: solo errores en consola")

    try:
        server = Server()
        registrar_jugadores(server, host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
        sys.exit(0)
    except (OSError, ValueError, RuntimeError):
        logger.exception("Error al iniciar el servidor")
        sys.exit(1)


if __name__ == "__main__":
    main()
