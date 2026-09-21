"""Módulo para gestión de clientes del servidor.

Este módulo encapsula la lógica de registro y gestión de clientes,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client


class ServerClientRegistry:
    """Gestiona el registro y almacenamiento de clientes conectados.

    Esta clase se encarga de todas las operaciones relacionadas con
    el almacenamiento y consulta de clientes, separando esta responsabilidad
    del Server principal.
    """

    def __init__(self) -> None:
        """Inicializa el registro de clientes."""
        self._clients: dict[int, Client] = {}
        self._lock = threading.RLock()

    def registrar_cliente(self, user_id: int, client: Client) -> bool:
        """Registra un nuevo cliente en el servidor.

        Args:
            user_id: ID único del cliente.
            client: Objeto cliente a registrar.

        Returns:
            ``True`` si se incorporó el cliente; ``False`` si el ID ya estaba
            registrado.

        """
        with self._lock:
            if user_id in self._clients:
                return False
            self._clients[user_id] = client
            return True

    def desconectar_cliente(
        self, user_id: int, expected_client: Client | None = None
    ) -> Client | None:
        """Desconecta un cliente del servidor.

        Args:
            user_id: ID del cliente a desconectar.
            expected_client: Cliente que solicita la baja. Si se indica, evita
                retirar una conexión más nueva que reutilice el mismo ID.

        Returns:
            El cliente que se retiró, o ``None`` si ya había sido retirado.

        """
        with self._lock:
            current_client = self._clients.get(user_id)
            if expected_client is not None and current_client is not expected_client:
                return None
            return self._clients.pop(user_id, None)

    def obtener_cliente(self, user_id: int) -> Client | None:
        """Obtiene un cliente por su ID.

        Args:
            user_id: ID del cliente.

        Returns:
            Cliente si existe, None en caso contrario.

        """
        with self._lock:
            return self._clients.get(user_id)

    def obtener_todos(self) -> list[Client]:
        """Obtiene la lista de todos los clientes conectados.

        Returns:
            Lista de clientes.

        """
        with self._lock:
            return list(self._clients.values())

    def obtener_ids(self) -> list[int]:
        """Obtiene la lista de IDs de clientes conectados.

        Returns:
            Lista de IDs de clientes.

        """
        with self._lock:
            return list(self._clients.keys())

    def cantidad(self) -> int:
        """Obtiene la cantidad de clientes conectados.

        Returns:
            Cantidad de clientes conectados.

        """
        with self._lock:
            return len(self._clients)

    def contiene(self, user_id: int) -> bool:
        """Verifica si un cliente está registrado.

        Args:
            user_id: ID del cliente a verificar.

        Returns:
            True si el cliente está registrado, False en caso contrario.

        """
        with self._lock:
            return user_id in self._clients
