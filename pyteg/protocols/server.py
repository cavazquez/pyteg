"""Protocolo del servidor visto desde las tareas (`ServerLikeProtocol`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyteg.server.juego.state_validator import HasEstado

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.protocols.client import IClientProtocol
    from pyteg.protocols.game import IGameProtocol
    from pyteg.protocols.mapa import IMapProtocol
    from pyteg.server.msg.types import BattleResultPayload, MissileResultPayload


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

    def enviar_resultado_batalla(self, resultado: BattleResultPayload) -> None:
        """Envía el resultado de una batalla a todos los clientes."""
        ...

    def enviar_resultado_misil(self, resultado: MissileResultPayload) -> None:
        """Envía el resultado del lanzamiento de un misil a todos los clientes."""
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

    # --- Métodos del servidor consumidos por las tareas del lobby ---

    def enviar_chat(self, username: str, msg: str | None) -> None:
        """Envía un mensaje de chat a todos los clientes."""
        ...

    def enviar_estado(self) -> None:
        """Envía el estado actual del servidor a todos los clientes."""
        ...

    def enviar_username(self) -> None:
        """Envía los nombres de usuario a todos los clientes."""
        ...

    def enviar_colores_asignados(self) -> None:
        """Envía los colores asignados a todos los clientes."""
        ...

    def empezar_partida(self) -> None:
        """Inicia la partida en el servidor."""
        ...

    def set_segundos_por_turno(self, segundos: int) -> None:
        """Configura los segundos por turno."""
        ...

    def set_paises_para_victoria(self, paises: int) -> None:
        """Configura la cantidad de países necesarios para ganar."""
        ...

    def set_objetivos_secretos(self, *, activados: bool) -> None:
        """Activa/desactiva los objetivos secretos."""
        ...

    def set_misiles_habilitados(self, *, activados: bool) -> None:
        """Habilita/deshabilita los misiles."""
        ...

    @property
    def color(self) -> object:
        """Servicio de gestión de colores del servidor."""
        ...
