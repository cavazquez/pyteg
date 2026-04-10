"""Módulo para construir clientes en el servidor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.debug_logger import debug_logger
from pyteg.server_client import Client

if TYPE_CHECKING:
    from pyteg.server_client_connection import ConnectionServer
    from pyteg.server_estado import Estado


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


class ServerBuildClient:
    """Construye instancias de clientes para el servidor."""

    def __init__(self) -> None:
        """Inicializa el constructor de clientes con un contador de user_id."""
        self._user_id = 1
        debug_logger.log(
            f"ServerBuildClient: Nueva instancia creada, "
            f"_user_id inicial: {self._user_id}"
        )
        # Ya no usamos la lista de nombres predefinidos
        # ya que el cliente proporcionará su propio nombre de usuario

    def build(
        self,
        connection: ConnectionServer,
        server: ServerLike,
        username: str | None = None,
    ) -> tuple[int, Client]:
        """Construye un nuevo cliente y lo registra en el servidor.

        Args:
            connection: Conexión del servidor con el cliente.
            server: Instancia del servidor.
            username: Nombre de usuario (opcional). Si no se proporciona,
                se genera uno genérico.

        Returns:
            Tupla con (user_id, Client) del cliente creado.

        """
        # Si no se proporciona un nombre de usuario, usar uno genérico
        if not username:
            username = f"Jugador_{self._user_id}"

        user_id = self._user_id
        debug_logger.log(f"ServerBuildClient: Asignando user_id {user_id} a {username}")
        self._user_id += 1
        debug_logger.log(f"ServerBuildClient: Próximo user_id será: {self._user_id}")
        es_admin = user_id == 1
        client = Client(user_id, connection, server, username, soy_admin=es_admin)
        return user_id, client
