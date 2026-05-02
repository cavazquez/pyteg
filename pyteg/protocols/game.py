"""Protocolo del juego (`IGameProtocol`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pyteg.core.turnos.protocol import ITurno
    from pyteg.protocols.client import IClientProtocol
    from pyteg.protocols.mapa import IMapProtocol


class IGameProtocol(Protocol):
    """Protocolo para objetos de juego.

    Define la interfaz mínima que debe implementar un objeto de juego
    para ser usado en las tareas del servidor.
    """

    def empezo(self) -> bool:
        """Verifica si el juego ha comenzado.

        Returns:
            True si el juego ha comenzado, False en caso contrario.

        """
        ...

    def turno_actual(self) -> ITurno:
        """Obtiene el turno actual.

        Returns:
            El turno actual.

        """
        ...

    def turnos(self) -> Sequence[ITurno]:
        """Obtiene la lista de turnos.

        Returns:
            Lista de turnos.

        """
        ...

    def id_turno_actual(self) -> int:
        """Obtiene el índice del turno actual.

        Returns:
            Índice del turno actual.

        """
        ...

    def num_ronda(self) -> int:
        """Obtiene el número de ronda actual.

        Returns:
            Número de ronda.

        """
        ...

    def mazo(self) -> object:  # Mazo, pero evitamos import circular
        """Obtiene el mazo de tarjetas.

        Returns:
            El mazo de tarjetas.

        """
        ...

    def atacar(
        self,
        pais_atacante: str,
        pais_defensor: str,
        cantidad_unidades: int | None = None,
    ) -> dict[str, Any]:
        """Realiza un ataque entre dos países.

        Args:
            pais_atacante: País que ataca.
            pais_defensor: País que defiende.
            cantidad_unidades: Cantidad de unidades que atacan (None = máximo).

        Returns:
            Diccionario con el resultado del ataque.

        """
        ...

    def marcar_jugador_puede_reclamar(self, jugador: IClientProtocol) -> None:
        """Marca que un jugador puede reclamar una tarjeta.

        Args:
            jugador: Jugador que puede reclamar.

        """
        ...

    def puede_reclamar_tarjeta(self, jugador: IClientProtocol) -> bool:
        """Verifica si un jugador puede reclamar una tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si puede reclamar, False en caso contrario.

        """
        ...

    def dame_una_tarjeta(self, jugador: IClientProtocol) -> None:
        """Asigna una tarjeta a un jugador.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        ...

    def reclamar_tarjeta_jugador(self, jugador: IClientProtocol) -> None:
        """Reclama una tarjeta para un jugador.

        Args:
            jugador: Jugador que reclama la tarjeta.

        """
        ...

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas."""
        ...

    def finalizar_turno(self) -> None:
        """Finaliza el turno actual."""
        ...

    def mapa(self) -> IMapProtocol:
        """Obtiene el mapa del juego.

        Returns:
            El mapa del juego.

        """
        ...
