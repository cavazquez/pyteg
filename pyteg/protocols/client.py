"""Protocolo del cliente del lado del servidor (`IClientProtocol`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.protocols.server import ServerLikeProtocol
    from pyteg.server.conexion.transmisor import ServerTransmisor


class IClientProtocol(Protocol):
    """Protocolo para objetos cliente del servidor.

    Define la interfaz mínima que debe implementar un cliente para ser
    usado en las tareas del servidor, el broadcaster, los servicios de
    color y todo el código que históricamente recibía `client: Any`.
    """

    @property
    def transmisor(self) -> ServerTransmisor:
        """Transmisor de mensajes del cliente."""
        ...

    @property
    def server(self) -> ServerLikeProtocol:
        """Referencia al servidor."""
        ...

    def userid(self) -> int:
        """Devuelve el `userid` (int) del cliente."""
        ...

    def username(self) -> str:
        """Devuelve el nombre de usuario (UI/chat)."""
        ...

    def set_username(self, username: str) -> None:
        """Cambia el nombre de usuario."""
        ...

    def cambiar_color(self, color: str) -> None:
        """Solicita asignar un color (`#RRGGBB`)."""
        ...

    def asignar_color(self, color: IColor | None) -> None:
        """Asigna directamente un objeto `IColor` al cliente."""
        ...

    def color_actual(self) -> IColor | None:
        """Devuelve el color actual del cliente, si lo tiene."""
        ...
