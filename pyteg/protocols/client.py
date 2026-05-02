"""Protocolo del cliente del lado del servidor (`IClientProtocol`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pyteg.protocols.server import ServerLikeProtocol
    from pyteg.server.conexion.transmisor import ServerTransmisor


class IClientProtocol(Protocol):
    """Protocolo para objetos cliente del servidor.

    Define la interfaz mínima que debe implementar un cliente
    para ser usado en las tareas del servidor.
    """

    @property
    def transmisor(self) -> ServerTransmisor:
        """Transmisor de mensajes del cliente."""
        ...

    @property
    def server(self) -> ServerLikeProtocol:
        """Referencia al servidor."""
        ...
