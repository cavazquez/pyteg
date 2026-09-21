"""Rutina para registrar jugadores entrantes."""

from __future__ import annotations

import socket
import threading
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Protocol

from pyteg.codecs_utils import NulDelimitedUtf8Codec
from pyteg.logger import get_logger
from pyteg.server.conexion.build_cliente import ServerBuildClient
from pyteg.server.conexion.connection import ConnectionServer
from pyteg.server.msg import MsgError

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.estado import Estado


class ServerLike(Protocol):
    """Protocolo que define la interfaz mínima requerida del servidor."""

    estado: Estado

    def registrar_cliente(self, user_id: Any, client: Any) -> bool:
        """Registra un cliente en el servidor.

        Args:
            user_id: ID del usuario.
            client: Cliente a registrar.

        Returns:
            ``True`` si el cliente fue aceptado.

        """
        ...

    def registrar_reconexion_pendiente(self, user_id: Any, client: Any) -> bool:
        """Registra una conexión temporal durante una partida."""
        ...


def _rechazar_conexion(
    conn: socket.socket,
    error_type: str,
    message: str,
    logger: Any,
) -> None:
    """Envía un error JSON normalizado y libera el socket entrante."""
    try:
        payload = MsgError(error_type, message).to_json()
        conn.sendall(NulDelimitedUtf8Codec.encode_frame(payload))
    except OSError:
        logger.exception("Error al enviar el rechazo de conexión")
    finally:
        conn.close()


def _iniciar_cliente(
    server: ServerLike,
    builder: ServerBuildClient,
    conn: socket.socket,
    addr: tuple[str, int],
    logger: Any,
) -> None:
    """Registra un cliente aceptado y arranca su hilo de recepción."""
    connection = ConnectionServer(conn, addr)
    client: Client | None = None
    try:
        user_id, client = builder.build(connection, server)
        if server.estado.es_jugando():
            accepted = server.registrar_reconexion_pendiente(user_id, client)
            error_type = "game_in_progress"
            error_message = (
                "La partida ya comenzó. Sólo se aceptan reconexiones de jugadores "
                "desconectados."
            )
        else:
            accepted = server.registrar_cliente(user_id, client)
            error_type = "room_full"
            error_message = "La sala está completa. Intenta nuevamente más tarde."

        if not accepted:
            client.transmisor.enviar_error(
                error_type,
                error_message,
            )
            client.cerrar(flush_outgoing=True)
            return

        client_thread = threading.Thread(target=client.run, daemon=True)
        client_thread.start()
        logger.info("Cliente %s conectado y en ejecución", user_id)
    except Exception:
        if client is not None:
            client.cerrar()
        else:
            connection.close()
        raise


def registrar_jugadores(
    server: ServerLike, host: str = "127.0.0.1", port: int = 65432
) -> None:
    """Inicia el servidor para aceptar conexiones de jugadores."""
    logger = get_logger("server.registrar_jugadores")
    logger.info("Iniciando servidor de jugadores en %s:%s", host, port)

    server_build_client = ServerBuildClient()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen()

        while True:
            try:
                logger.debug("Esperando conexiones en %s:%s...", host, port)
                conn, addr = server_socket.accept()
            except KeyboardInterrupt:
                logger.info("Deteniendo el servidor por interrupción del usuario")
                break
            except Exception:
                logger.exception("Error al aceptar una conexión")
                continue

            logger.info("Nueva conexión aceptada desde %s", addr)
            try:
                if server.estado.es_finalizado():
                    estado_actual = server.estado.estado_actual()
                    logger.warning(
                        "Rechazando conexión de %s: "
                        "El juego ya está en progreso (estado: %s)",
                        addr,
                        estado_actual,
                    )
                    _rechazar_conexion(
                        conn,
                        "game_in_progress",
                        "El juego ya está en progreso y ya finalizó.",
                        logger,
                    )
                    continue
                _iniciar_cliente(server, server_build_client, conn, addr, logger)
            except Exception:
                logger.exception("Error al manejar la conexión")
                with suppress(OSError):
                    conn.close()

    except (OSError, RuntimeError) as exc:
        logger.critical("Error crítico en el servidor: %s", exc, exc_info=True)
    finally:
        logger.info("Cerrando el servidor...")
        server_socket.close()
