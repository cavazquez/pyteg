"""Módulo principal del servidor del juego."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING, Any

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.core.cartas.mazo import Mazo
from pyteg.core.mapa.build_mapa import build_mapa_from_reader
from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
from pyteg.log_cli import add_log_arguments
from pyteg.logger import get_logger
from pyteg.protocol import PROTOCOL_VERSION, SNAPSHOT_VERSION, map_hash_for_theme
from pyteg.server.conexion.broadcaster import ServerMessageBroadcaster
from pyteg.server.conexion.registrar_jugadores import registrar_jugadores
from pyteg.server.conexion.registry import ServerClientRegistry
from pyteg.server.juego import session_sync
from pyteg.server.juego.color import ServerColor
from pyteg.server.juego.command_executor import GameCommandExecutor
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

    def __init__(self, theme: str = DEFAULT_MAP_THEME) -> None:
        """Inicializa el servidor con mapa, mazo y configuración inicial."""
        self.protocol_version = PROTOCOL_VERSION
        self.theme = theme
        self._state_revision = 0
        self._client_registry = ServerClientRegistry()
        self.color = ServerColor()
        self.estado = Estado()
        self._broadcaster = ServerMessageBroadcaster(self.dame_clientes)

        toml_reader = TomlReader.from_theme(theme, strict=True)
        self.mapa = Mapa(lambda: build_mapa_from_reader(toml_reader))
        self.mazo = Mazo(self.mapa.paises(), toml_reader.get_simbolos())
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
        self._command_executor = GameCommandExecutor(self)
        self._command_executor.start()

    def map_hash(self) -> str:
        """Identificador estable de las reglas públicas del mapa.

        Returns:
            Hash SHA-256 del mapa configurado.

        """
        return map_hash_for_theme(self.theme)

    def state_revision(self) -> int:
        """Revisión pública actual del estado del juego.

        Returns:
            Número de revisión monotónico.

        """
        return self._state_revision

    def bump_state_revision(self) -> int:
        """Avanza la revisión una vez finalizada una transición serializada.

        Returns:
            Nueva revisión pública.

        """
        self._state_revision += 1
        return self._state_revision

    def public_snapshot(self) -> dict[str, Any]:
        """Construye un snapshot público completo y autocontenido.

        El snapshot se construye mientras el ejecutor de comandos posee la
        transición. Nunca incluye cartas ni objetivos secretos; esos datos se
        envían por mensajes privados separados.

        Returns:
            Diccionario JSON serializable del estado público.

        """
        game = self.game
        countries = {
            pais: {
                "userid": self.mapa.ocupado_por(pais),
                "unidades": self.mapa.cantidad_unidades(pais),
                "misiles": self.mapa.cantidad_misiles(pais),
            }
            for pais in self.mapa.paises()
        }
        historicos = game.jugadores() if game is not None else self.dame_clientes()
        conectados = {int(client.userid()) for client in self.dame_clientes()}
        players: list[dict[str, Any]] = []
        for client in historicos:
            color = client.color_actual()
            color_data = json.loads(color.to_json()) if color is not None else None
            es_admin = getattr(client, "es_admin", lambda: False)
            eliminado = game is not None and game.jugador_esta_eliminado(client)
            players.append({
                "userid": int(client.userid()),
                "username": client.username(),
                "color": color_data,
                "admin": bool(es_admin()) if callable(es_admin) else False,
                "connected": int(client.userid()) in conectados,
                "eliminated": bool(eliminado),
            })
        fase: str | None = None
        turno_data: dict[str, int | None] | None = None
        refuerzos_pendientes = 0
        if game is not None and game.empezo():
            turno = game.turno_actual()
            fase = game.fase_actual()
            turno_data = {
                "num_turno": game.id_turno_actual(),
                "num_ronda": game.num_ronda(),
                "jugador_id": int(turno.jugador_actual()),
            }
            refuerzos_pendientes = game.refuerzos_pendientes()
        snapshot: dict[str, Any] = {
            "snapshot_version": SNAPSHOT_VERSION,
            "revision": self.state_revision(),
            "estado": self.estado.estado_actual(),
            "theme": self.theme,
            "map_hash": self.map_hash(),
            "configuracion": self._game_coordinator.configuracion_partida(),
            "players": players,
            "countries": countries,
            "fase": fase,
            "turno": turno_data,
            "refuerzos_pendientes": refuerzos_pendientes,
        }
        return snapshot

    def enviar_snapshot(self) -> None:
        """Difunde el snapshot público actual."""
        self._broadcaster.enviar_snapshot(self.public_snapshot())

    def validar_handshake(self, client: Client, data: dict[str, Any]) -> bool:
        """Valida protocolo, tema y mapa antes de iniciar una partida.

        Returns:
            ``True`` si el cliente puede participar en la sala.

        """
        expected_hash = self.map_hash()
        checks = (
            (
                data.get("protocol_version") == self.protocol_version,
                "incompatible_protocol",
                "La versión de protocolo no es compatible.",
            ),
            (
                data.get("theme") == self.theme,
                "incompatible_theme",
                "El tema solicitado no coincide con el servidor.",
            ),
            (
                data.get("map_hash") == expected_hash,
                "incompatible_map",
                "El mapa del cliente no coincide con el servidor.",
            ),
        )
        for accepted, code, message in checks:
            if not accepted:
                client.marcar_handshake(False)  # noqa: FBT003
                client.transmisor.enviar_error(code, message)
                client.transmisor.enviar_hello_ack(accepted=False)
                return False
        client.marcar_handshake(True)  # noqa: FBT003
        client.transmisor.enviar_hello_ack()
        return True

    @property
    def game(self) -> Game | None:
        """Obtiene la instancia del juego actual.

        Returns:
            Instancia del juego o None si no ha comenzado.

        """
        return self._game_coordinator.game()

    def encolar_comando(self, client: Client, data: dict[str, Any]) -> None:
        """Encola un comando TCP para ejecutarlo en la transición serializada."""
        self._command_executor.enqueue_command(client, data)

    def encolar_vencimiento_turno(self, generation: int) -> None:
        """Encola un vencimiento asociado al turno que lo originó."""
        self._command_executor.enqueue_turn_expired(generation)

    def encolar_desconexion_jugador(self, user_id: int) -> None:
        """Encola la baja de un jugador para actualizar sus turnos."""
        self._command_executor.enqueue_client_disconnected(user_id)

    def turno_snapshot(self) -> tuple[int, int] | None:
        """Obtiene ``(jugador_actual, generación)`` sin leer el juego en el timer.

        Returns:
            El jugador del turno actual y su generación, o ``None`` sin partida.

        """
        return self._command_executor.turn_snapshot()

    def detener(self) -> None:
        """Detiene el temporizador y el ejecutor de transiciones del servidor."""
        self._game_coordinator.detener()
        self._command_executor.stop()

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

    def quitarme(self, user_id: int, expected_client: Client | None = None) -> None:
        """Retira una conexión y libera su color cuando corresponde.

        Args:
            user_id: ID del cliente a desconectar.
            expected_client: Conexión que solicita la baja. Impide que un cierre
                tardío retire a otro cliente con el mismo ID.

        """
        client = self._client_registry.desconectar_cliente(user_id, expected_client)
        if client is None:
            return

        LOGGER.info("Quitando cliente %s", user_id)
        if self.estado.es_jugando():
            LOGGER.info(
                "Se conserva el color de %s porque la partida sigue activa", user_id
            )
            self.encolar_desconexion_jugador(user_id)
        else:
            self.color.liberar_color(client.color_actual())
            if self.estado.es_inicial() or self.estado.es_esperando_jugadores():
                self._promover_administrador()

        # Notificar a todos los clientes restantes sobre la desconexión
        self.enviar_username()

    def registrar_cliente(self, user_id: int, client: Client) -> bool:
        """Registra un nuevo cliente en el servidor.

        Args:
            user_id: ID único del cliente.
            client: Objeto cliente a registrar.

        Returns:
            ``True`` si se reservó un color y se registró al cliente. Devuelve
            ``False`` si la sala no tiene capacidad.

        """
        # Asignar color antes de registrar. El orden del registro es la única
        # fuente de desempate para la sucesión del administrador.
        habia_clientes = self.cant_clients() > 0
        if not self.color.asignar_color_aleatorio(client):
            LOGGER.warning("Sala llena; no se puede registrar el cliente %s", user_id)
            return False

        if self._client_registry.registrar_cliente(user_id, client):
            if not habia_clientes:
                self._promover_administrador(notificar=False)
            return True

        self.color.liberar_color(client.color_actual())
        LOGGER.warning("ID de cliente duplicado al registrar %s", user_id)
        return False

    def _promover_administrador(self, *, notificar: bool = True) -> None:
        """Garantiza un único administrador mientras la sala es un lobby."""
        clientes = self.dame_clientes()
        if not clientes:
            return
        admin = clientes[0]
        for candidato in clientes:
            asignar = getattr(candidato, "asignar_admin", None)
            if callable(asignar):
                asignar(candidato is admin)
        if not notificar:
            return
        sos_admin = getattr(getattr(admin, "transmisor", None), "sos_admin", None)
        if callable(sos_admin):
            sos_admin()

    def promover_administrador(self) -> None:
        """Expone la sucesión para reabrir un lobby tras una partida."""
        self._promover_administrador()

    def registrar_reconexion_pendiente(self, user_id: int, client: Client) -> bool:
        """Registra una conexión temporal sin asignarle un color nuevo.

        Returns:
            ``True`` si la conexión quedó pendiente; ``False`` si no hay partida
            activa o capacidad para el handshake.

        """
        game = self.game
        if not self.estado.es_jugando() or game is None or not game.empezo():
            return False
        if self.cant_clients() >= len(self.color.colores()):
            return False
        client.marcar_reconexion_pendiente()
        if self._client_registry.registrar_cliente(user_id, client):
            return True
        client.marcar_reconexion_pendiente(pendiente=False)
        return False

    def reconectar_cliente(  # noqa: C901, PLR0911
        self, client: Client, user_id: int, token: str
    ) -> bool:
        """Autentica una conexión pendiente y restaura su sesión de juego.

        Returns:
            ``True`` si se reemplazó la conexión histórica; ``False`` si el
            token o la identidad no son válidos.

        """
        game = self.game
        if game is None or not client.es_reconexion_pendiente():
            return False
        if not game.token_de_sesion_valido(user_id, token):
            return False

        # La baja del socket y el comando de reconexión llegan desde hilos
        # distintos. Si el comando gana esa carrera, registrar la desconexión
        # dentro de la misma transición deja el estado listo para autenticar.
        if self._client_registry.obtener_cliente(
            int(user_id)
        ) is None and not game.jugador_esta_desconectado(int(user_id)):
            game.desconectar_jugador(int(user_id))
        if not game.puede_reconectar(int(user_id), token):
            return False

        temporary_user_id = int(client.userid())
        anterior = next(
            (
                jugador
                for jugador in game.jugadores()
                if int(jugador.userid()) == int(user_id)
            ),
            None,
        )
        if anterior is None:
            return False
        exportar_cache = getattr(anterior, "export_command_cache", None)
        importar_cache = getattr(client, "import_command_cache", None)
        if callable(exportar_cache) and callable(importar_cache):
            importar_cache(exportar_cache())
        else:
            exportar_resultados = getattr(anterior, "export_command_results", None)
            importar_resultados = getattr(client, "import_command_results", None)
            if callable(exportar_resultados) and callable(importar_resultados):
                importar_resultados(exportar_resultados())
        if not self._client_registry.reasignar_cliente(
            temporary_user_id, int(user_id), client
        ):
            return False

        client.reasignar_userid(int(user_id))
        if not game.reconectar_jugador(int(user_id), client, token):
            # El estado sólo puede fallar si cambió entre las dos validaciones;
            # devolver el registro temporal evita dejar una conexión huérfana.
            client.reasignar_userid(temporary_user_id)
            self._client_registry.reasignar_cliente(
                int(user_id), temporary_user_id, client
            )
            return False

        client.marcar_reconexion_pendiente(pendiente=False)
        client.transmisor.enviar_reconexion(int(user_id), temporary_user_id)
        client.transmisor.enviar_session_token(int(user_id), client.reconnect_token())
        client.transmisor.enviar_colores(self.color.colores())
        self.enviar_userid()
        self.enviar_username()
        self.enviar_colores_asignados()
        self.enviar_estado()
        self.enviar_configuracion_partida()
        self.enviar_turno_actual(incluir_mapa=False)
        client.transmisor.enviar_mapa(self.mapa, game)
        for pais in self.mapa.paises():
            cantidad_misiles = self.mapa.cantidad_misiles(pais)
            if cantidad_misiles > 0:
                client.transmisor.enviar_misil_agregado(pais, cantidad_misiles)
        self.enviar_tarjetas_jugador(client)
        return True

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
        session_sync.enviar_colores_asignados(self.game, self.dame_clientes)

    def actualizar_lista_jugadores_ui(self) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista para todos los clientes.
        """
        if self.game is None:
            return
        session_sync.actualizar_lista_jugadores_ui(self.game, self.dame_clientes)

    def enviar_estado(self) -> None:
        """Envía el estado actual del juego a todos los clientes."""
        self._broadcaster.enviar_estado(self.estado.estado_actual())

    def enviar_turno_actual(self, *, incluir_mapa: bool = True) -> None:
        """Envía el número de turno y ronda actuales a todos los clientes."""
        if not self.estado.es_jugando() or not self.game:
            return
        session_sync.enviar_turno_actual(
            self.game,
            self.dame_clientes,
            self._client_registry.obtener_cliente,
            self._broadcaster,
            self.mapa,
            incluir_mapa=incluir_mapa,
        )

    def enviar_chat(self, username: str, msg: str) -> None:
        """Envía un mensaje de chat a todos los clientes.

        Args:
            username: Nombre de usuario del remitente.
            msg: Mensaje de chat.

        """
        self._broadcaster.enviar_chat(username, msg)

    def enviar_sistema(self, msg: str) -> None:
        """Envía un aviso de sistema a todos los clientes conectados."""
        self._broadcaster.enviar_sistema(msg)

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

    def finalizar_partida(self) -> bool:
        """Finaliza la partida actual y detiene sus actualizaciones.

        Returns:
            ``True`` si el estado de la partida cambió a terminal.

        """
        changed = self._game_coordinator.finalizar_partida()
        if changed:
            self.bump_state_revision()
            self.enviar_snapshot()
        return changed

    def volver_al_lobby(self) -> bool:
        """Reabre el lobby y limpia todos los recursos de la partida.

        Returns:
            ``True`` si se cambió desde el estado finalizado.

        """
        return self._game_coordinator.volver_al_lobby(self)

    def enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador del turno actual."""
        if not self.estado.es_jugando() or not self.game:
            return
        session_sync.enviar_unidades_disponibles(
            self.game, self._client_registry.obtener_cliente
        )

    def enviar_fase(self) -> None:
        """Envía la fase autoritativa del turno a todos los clientes."""
        if not self.estado.es_jugando() or not self.game:
            return
        session_sync.enviar_fase(self.game, self.dame_clientes)

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

    parser.add_argument(
        "--theme",
        type=str,
        default=DEFAULT_MAP_THEME,
        help=(f"Tema de mapa en themes/ (predeterminado: {DEFAULT_MAP_THEME})"),
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

    theme_dir = get_resource_path(f"themes/{args.theme}")
    if not (theme_dir / "paises.toml").is_file():
        logger.error("Tema de mapa no encontrado: themes/%s/paises.toml", args.theme)
        sys.exit(1)

    server: Server | None = None
    try:
        server = Server(theme=args.theme)
        registrar_jugadores(server, host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
        sys.exit(0)
    except OSError, ValueError, RuntimeError:
        logger.exception("Error al iniciar el servidor")
        sys.exit(1)
    finally:
        if server is not None:
            server.detener()


if __name__ == "__main__":
    main()
