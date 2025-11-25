"""Rutina para registrar jugadores entrantes."""

from __future__ import annotations

import socket
import threading
from typing import TYPE_CHECKING, Any, Protocol

from src.logger import get_logger
from src.server_build_client import ServerBuildClient
from src.server_client_connection import ConnectionServer

if TYPE_CHECKING:
    from src.server_estado import Estado


class ServerLike(Protocol):
    """Protocolo que define la interfaz mínima requerida del servidor."""

    estado: Estado

    def registrar_cliente(self, user_id: Any, client: Any) -> None:
        """Registra un cliente en el servidor.

        Args:
            user_id: ID del usuario.
            client: Cliente a registrar.

        """
        ...


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
                logger.info("Nueva conexión aceptada desde %s", addr)

                if server.estado.es_jugando() or server.estado.es_finalizado():
                    estado_actual = server.estado.estado_actual()
                    logger.warning(
                        "Rechazando conexión de %s: "
                        "El juego ya está en progreso (estado: %s)",
                        addr,
                        estado_actual,
                    )
                    try:
                        mensaje_rechazo = (
                            "El juego ya está en progreso. "
                            "No se pueden conectar nuevos jugadores."
                        )
                        conn.send(mensaje_rechazo.encode("utf-8"))
                    except OSError:
                        logger.exception("Error al enviar mensaje de rechazo")
                    finally:
                        conn.close()
                    continue

                connection = ConnectionServer(conn, addr)
                user_id, client = server_build_client.build(connection, server)
                server.registrar_cliente(user_id, client)

                client_thread = threading.Thread(target=client.run, daemon=True)
                client_thread.start()
                logger.info("Cliente %s conectado y en ejecución", user_id)

            except KeyboardInterrupt:
                logger.info("Deteniendo el servidor por interrupción del usuario")
                break
            except Exception:
                logger.exception("Error al manejar la conexión")

    except (OSError, RuntimeError) as exc:
        logger.critical("Error crítico en el servidor: %s", exc, exc_info=True)
    finally:
        logger.info("Cerrando el servidor...")
        server_socket.close()
