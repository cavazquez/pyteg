"""Módulo para gestión de clientes del servidor.

Este módulo encapsula la lógica de registro y gestión de clientes,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server_client import Client


class ServerClientRegistry:
    """Gestiona el registro y almacenamiento de clientes conectados.

    Esta clase se encarga de todas las operaciones relacionadas con
    el almacenamiento y consulta de clientes, separando esta responsabilidad
    del Server principal.
    """

    def __init__(self) -> None:
        """Inicializa el registro de clientes."""
        self._clients: dict[int, Client] = {}

    def registrar_cliente(self, user_id: int, client: Client) -> None:
        """Registra un nuevo cliente en el servidor.

        Args:
            user_id: ID único del cliente.
            client: Objeto cliente a registrar.

        """
        self._clients[user_id] = client

    def desconectar_cliente(self, user_id: int) -> None:
        """Desconecta un cliente del servidor.

        Args:
            user_id: ID del cliente a desconectar.

        """
        self._clients.pop(user_id, None)

    def obtener_cliente(self, user_id: int) -> Client | None:
        """Obtiene un cliente por su ID.

        Args:
            user_id: ID del cliente.

        Returns:
            Cliente si existe, None en caso contrario.

        """
        return self._clients.get(user_id)

    def obtener_todos(self) -> list[Client]:
        """Obtiene la lista de todos los clientes conectados.

        Returns:
            Lista de clientes.

        """
        return list(self._clients.values())

    def obtener_ids(self) -> list[int]:
        """Obtiene la lista de IDs de clientes conectados.

        Returns:
            Lista de IDs de clientes.

        """
        return list(self._clients.keys())

    def cantidad(self) -> int:
        """Obtiene la cantidad de clientes conectados.

        Returns:
            Cantidad de clientes conectados.

        """
        return len(self._clients)

    def contiene(self, user_id: int) -> bool:
        """Verifica si un cliente está registrado.

        Args:
            user_id: ID del cliente a verificar.

        Returns:
            True si el cliente está registrado, False en caso contrario.

        """
        return user_id in self._clients
