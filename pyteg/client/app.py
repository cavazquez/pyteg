"""Modelo minimalista de cliente."""

from __future__ import annotations


class Client:
    """Cliente del juego que representa a un jugador."""

    def __init__(self) -> None:
        """Inicializa un nuevo cliente."""
        self._username: str | None = None
        self._userid: int | None = None
        self._es_admin = False

    def set_username(self, username: str) -> None:
        """Establece el nombre de usuario del cliente."""
        self._username = username

    def set_userid(self, userid: int) -> None:
        """Establece el ID de usuario del cliente."""
        self._userid = int(userid)

    def username(self) -> str | None:
        """Obtiene el nombre de usuario del cliente.

        Returns:
            Nombre de usuario o None si no está asignado.

        """
        return self._username

    def userid(self) -> int | None:
        """Obtiene el ID de usuario del cliente.

        Returns:
            ID de usuario del cliente, o None si no está asignado.

        """
        return self._userid

    def es_admin(self) -> bool:
        """Verifica si el cliente es administrador.

        Returns:
            True si es administrador, False en caso contrario.

        """
        return self._es_admin

    def ahora_es_admin(self) -> None:
        """Marca al cliente como administrador."""
        self._es_admin = True
