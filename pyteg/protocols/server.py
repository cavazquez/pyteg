"""Protocolo del servidor visto desde las tareas (`ServerLikeProtocol`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.server.juego.state_validator import HasEstado

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.protocols.client import IClientProtocol
    from pyteg.protocols.game import IGameProtocol
    from pyteg.protocols.mapa import IMapProtocol


class ServerLikeProtocol(HasEstado, Protocol):
    """Protocolo para objetos que actúan como servidor.

    Define la interfaz mínima que debe implementar un objeto servidor
    para ser usado en las tareas del servidor.
    Extiende HasEstado para compatibilidad con validadores.
    """

    @property
    def mapa(self) -> IMapProtocol:
        """Mapa del juego."""
        ...

    @property
    def game(self) -> IGameProtocol | None:
        """Juego actual (puede ser None si no ha comenzado)."""
        ...

    def enviar_mapa(self) -> None:
        """Envía el mapa actualizado a todos los clientes."""
        ...

    def enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador actual."""
        ...

    def enviar_resultado_batalla(self, resultado: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes."""
        ...

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de misil agregado."""
        ...

    def enviar_tarjetas_jugador(self, client: IClientProtocol) -> None:
        """Envía las tarjetas del jugador."""
        ...

    def enviar_turno_actual(self) -> None:
        """Envía el turno actual a todos los clientes."""
        ...

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados."""
        ...

    def dame_clientes(self) -> list[IClientProtocol]:
        """Obtiene la lista de clientes."""
        ...

    def userid(self) -> int:
        """Obtiene el ID de usuario del cliente.

        Returns:
            ID de usuario del cliente.

        """
        ...

    def username(self) -> str:
        """Obtiene el nombre de usuario del cliente.

        Returns:
            Nombre de usuario del cliente.

        """
        ...

    def es_admin(self) -> bool:
        """Verifica si el cliente es administrador.

        Returns:
            True si es administrador, False en caso contrario.

        """
        ...

    def color_actual(self) -> IColor | None:
        """Obtiene el color actual del cliente.

        Returns:
            Color actual del cliente o None.

        """
        ...
