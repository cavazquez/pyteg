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

    def reabrir_lobby_si_vacio(self) -> bool:
        """Reabre una partida finalizada sin clientes antes del registro."""
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
        if server.estado.es_jugando() or bool(
            getattr(server, "migration_sessions", {})
        ):
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


class PlayerListener:
    """Socket de jugadores con arranque y cierre explícitos para el anfitrión."""

    def __init__(
        self,
        server: ServerLike,
        host: str = "127.0.0.1",
        port: int = 65432,
        *,
        first_user_id: int = 1,
    ) -> None:
        """Reserva el puerto antes de anunciar que el anfitrión está disponible.

        Raises:
            OSError: Si no se puede reservar o utilizar el puerto TCP.

        """
        self.server = server
        self._builder = ServerBuildClient(first_user_id)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._socket.bind((host, port))
            self._socket.listen()
            self._socket.settimeout(0.2)
        except OSError:
            self._socket.close()
            raise
        self.port = int(self._socket.getsockname()[1])

    def start(self) -> None:
        """Acepta conexiones en un hilo propio sin bloquear la interfaz Qt."""
        self._thread = threading.Thread(
            target=self.run, name="pyteg-player-listener", daemon=True
        )
        self._thread.start()

    def run(self) -> None:
        """Mantiene el registro TCP existente y admite sesiones migradas."""
        logger = get_logger("server.registrar_jugadores")
        while not self._stop.is_set():
            try:
                conn, addr = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                if not self._stop.is_set():
                    logger.exception("Error al aceptar una conexión")
                break
            try:
                if (
                    self.server.estado.es_finalizado()
                    and not getattr(self.server, "migration_sessions", {})
                    and not self.server.reabrir_lobby_si_vacio()
                ):
                    _rechazar_conexion(
                        conn, "game_in_progress", "El juego ya finalizó.", logger
                    )
                    continue
                _iniciar_cliente(self.server, self._builder, conn, addr, logger)
            except Exception:
                logger.exception("Error al manejar la conexión")
                with suppress(OSError):
                    conn.close()

    def close(self) -> None:
        """Libera el puerto y espera el hilo de aceptación."""
        self._stop.set()
        self._socket.close()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)


def registrar_jugadores(
    server: ServerLike, host: str = "127.0.0.1", port: int = 65432
) -> None:
    """Mantiene la entrada del servidor independiente con el mismo listener."""
    logger = get_logger("server.registrar_jugadores")
    listener: PlayerListener | None = None
    try:
        listener = PlayerListener(server, host, port)
        listener.run()
    except KeyboardInterrupt:
        logger.info("Deteniendo el servidor por interrupción del usuario")
    except OSError, RuntimeError:
        logger.exception("Error crítico en el servidor")
    finally:
        if listener is not None:
            listener.close()
