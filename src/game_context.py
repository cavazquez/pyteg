"""Módulo para contexto de acceso a recursos del juego.

Este módulo proporciona una capa de abstracción para acceder a los recursos
del juego (mapa, game, etc.) sin acoplamiento directo al servidor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.server_game import Game
    from src.server_mapa import Mapa


class ServerLike(Protocol):
    """Protocolo para acceso a métodos del servidor necesarios para las tareas."""

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

    def enviar_tarjetas_jugador(self, client: Any) -> None:
        """Envía las tarjetas del jugador."""
        ...

    def enviar_turno_actual(self) -> None:
        """Envía el turno actual a todos los clientes."""
        ...

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados."""
        ...

    def dame_clientes(self) -> list[Any]:
        """Obtiene la lista de clientes."""
        ...


class GameContext:
    """Contexto de acceso a recursos del juego.

    Esta clase proporciona acceso controlado a los recursos del juego
    (mapa, game, etc.) sin exponer directamente el servidor, reduciendo
    el acoplamiento entre componentes.
    """

    def __init__(
        self,
        mapa: Mapa,
        game: Game | None,
        server: ServerLike,
    ) -> None:
        """Inicializa el contexto del juego.

        Args:
            mapa: Instancia del mapa del juego.
            game: Instancia del juego (puede ser None si no ha comenzado).
            server: Referencia al servidor para métodos de notificación.

        """
        self._mapa = mapa
        self._game = game
        self._server = server

    @property
    def mapa(self) -> Mapa:
        """Obtiene el mapa del juego.

        Returns:
            Instancia del mapa.

        """
        return self._mapa

    @property
    def game(self) -> Game | None:
        """Obtiene el juego actual.

        Returns:
            Instancia del juego o None si no ha comenzado.

        """
        return self._game

    def enviar_mapa(self) -> None:
        """Envía el mapa actualizado a todos los clientes."""
        self._server.enviar_mapa()

    def enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador actual."""
        self._server.enviar_unidades_disponibles()

    def enviar_resultado_batalla(self, resultado: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes.

        Args:
            resultado: Diccionario con el resultado de la batalla.

        """
        self._server.enviar_resultado_batalla(resultado)

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de misil agregado.

        Args:
            pais: País donde se agregó el misil.
            cantidad_misiles: Cantidad total de misiles.

        """
        self._server.enviar_misil_agregado(pais, cantidad_misiles)

    def enviar_tarjetas_jugador(self, client: Any) -> None:
        """Envía las tarjetas del jugador.

        Args:
            client: Cliente al que enviar las tarjetas.

        """
        self._server.enviar_tarjetas_jugador(client)

    def enviar_turno_actual(self) -> None:
        """Envía el turno actual a todos los clientes."""
        self._server.enviar_turno_actual()

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados.

        Returns:
            True si los misiles están habilitados.

        """
        return self._server.misiles_habilitados()

    def dame_clientes(self) -> list[Any]:
        """Obtiene la lista de clientes.

        Returns:
            Lista de clientes.

        """
        return self._server.dame_clientes()
