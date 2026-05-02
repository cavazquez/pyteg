"""Validadores reutilizables para tareas del servidor.

Este módulo proporciona validadores que pueden ser reutilizados
en múltiples tareas del servidor para evitar duplicación de código.
"""

from typing import TYPE_CHECKING

from pyteg.config import FIRST_TURNS_NO_ATTACK
from pyteg.exception import (
    CountryNotOwnedError,
    GameNotStartedError,
    GameRuleViolationError,
    InvalidActionError,
    NotPlayerTurnError,
)
from pyteg.turnos import PrimerTurno, SegundoTurno

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol, IGameProtocol, IMapProtocol
    from pyteg.server.conexion.cliente import Client
    from pyteg.server.juego.game import Game
    from pyteg.server.juego.mapa import Mapa

# Alias para compatibilidad
ValidationError = GameRuleViolationError


class TurnValidator:
    """Valida que sea el turno del jugador correcto."""

    @staticmethod
    def validate_turn(
        client: "Client | IClientProtocol",
        game: "Game | IGameProtocol | None",
    ) -> None:
        """Valida que el juego haya comenzado y sea el turno del cliente.

        Args:
            client: Cliente que intenta realizar la acción.
            game: Instancia del juego o None si no ha comenzado.

        Raises:
            GameNotStartedError: Si el juego no ha comenzado.
            NotPlayerTurnError: Si no es el turno del cliente.

        """
        if game is None:
            raise GameNotStartedError

        turno_actual = game.turno_actual()
        jugador_actual = turno_actual.jugador_actual()
        if jugador_actual is None:
            raise NotPlayerTurnError
        client_userid = client.userid() if hasattr(client, "userid") else None
        if client_userid is None:
            raise NotPlayerTurnError
        if (
            not hasattr(jugador_actual, "userid")
            or jugador_actual.userid() != client_userid
        ):
            raise NotPlayerTurnError


class GameStateValidator:
    """Valida el estado del juego."""

    @staticmethod
    def validate_game_started(
        game: "Game | IGameProtocol | None",
    ) -> None:
        """Valida que el juego haya comenzado.

        Args:
            game: Instancia del juego o None si no ha comenzado.

        Raises:
            GameNotStartedError: Si el juego no ha comenzado.

        """
        if game is None:
            raise GameNotStartedError


class CountryOwnershipValidator:
    """Valida la propiedad de países."""

    @staticmethod
    def validate_ownership(
        client: "Client | IClientProtocol",
        mapa: "Mapa | IMapProtocol",
        pais: str,
        error_message: str | None = None,
    ) -> None:
        """Valida que el cliente sea dueño del país.

        Args:
            client: Cliente que intenta realizar la acción.
            mapa: Instancia del mapa del juego.
            pais: Nombre del país a validar.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            CountryNotOwnedError: Si el cliente no es dueño del país.

        """
        pais_owner_id = mapa.ocupado_por(pais)
        client_userid = client.userid() if hasattr(client, "userid") else None
        if client_userid is None:
            raise CountryNotOwnedError(pais, error_message)
        client_id = str(client_userid)
        if pais_owner_id != client_id:
            raise CountryNotOwnedError(pais, error_message)

    @staticmethod
    def validate_not_own_country(
        client: "Client | IClientProtocol",
        mapa: "Mapa | IMapProtocol",
        pais: str,
        error_message: str | None = None,
    ) -> None:
        """Valida que el cliente NO sea dueño del país.

        Args:
            client: Cliente que intenta realizar la acción.
            mapa: Instancia del mapa del juego.
            pais: Nombre del país a validar.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si el cliente es dueño del país.

        """
        pais_owner_id = mapa.ocupado_por(pais)
        client_userid = client.userid() if hasattr(client, "userid") else None
        if client_userid is None:
            return
        client_id = str(client_userid)
        if pais_owner_id == client_id:
            msg = error_message or f"No puedes atacar tu propio país: {pais}"
            raise InvalidActionError(msg)


class AdjacencyValidator:
    """Valida adyacencia entre países."""

    @staticmethod
    def validate_adjacent(
        mapa: "Mapa | IMapProtocol",
        origen: str,
        destino: str,
        error_message: str | None = None,
    ) -> None:
        """Valida que dos países sean adyacentes.

        Args:
            mapa: Instancia del mapa del juego.
            origen: País de origen.
            destino: País de destino.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si los países no son adyacentes.

        """
        paises_adyacentes = mapa.obtener_paises_adyacentes(origen)
        if destino not in paises_adyacentes:
            msg = error_message or f"{destino} no es adyacente a {origen}"
            raise InvalidActionError(msg)


class UnitValidator:
    """Valida unidades y cantidades."""

    @staticmethod
    def validate_min_units(
        mapa: "Mapa | IMapProtocol",
        pais: str,
        min_units: int,
        error_message: str | None = None,
    ) -> None:
        """Valida que un país tenga al menos una cantidad mínima de unidades.

        Args:
            mapa: Instancia del mapa del juego.
            pais: Nombre del país a validar.
            min_units: Cantidad mínima de unidades requeridas.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si el país no tiene suficientes unidades.

        """
        unidades = mapa.cantidad_unidades(pais)
        if unidades < min_units:
            msg = error_message or f"Necesitas al menos {min_units} unidades en {pais}"
            raise InvalidActionError(msg)

    @staticmethod
    def validate_sufficient_units_to_move(
        mapa: "Mapa | IMapProtocol",
        origen: str,
        cantidad: int,
        error_message: str | None = None,
    ) -> None:
        """Valida que haya suficientes unidades para mover sin vaciar el país.

        Args:
            mapa: Instancia del mapa del juego.
            origen: País de origen.
            cantidad: Cantidad de unidades a mover.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si no hay suficientes unidades para mover.

        """
        unidades_origen = mapa.cantidad_unidades(origen)
        if unidades_origen <= cantidad:
            msg = (
                error_message
                or f"No hay suficientes unidades en {origen} para mover {cantidad}"
            )
            raise InvalidActionError(msg)


class UnitTypeValidator:
    """Valida tipos de unidades."""

    @staticmethod
    def validate_unit_type(
        tipo_unidad: str, valid_types: set[str], error_message: str | None = None
    ) -> None:
        """Valida que el tipo de unidad sea válido.

        Args:
            tipo_unidad: Tipo de unidad a validar.
            valid_types: Conjunto de tipos válidos.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si el tipo de unidad no es válido.

        """
        if tipo_unidad not in valid_types:
            tipos_str = ", ".join(sorted(valid_types))
            msg = (
                error_message
                or f"Tipo de unidad no válido. Debe ser uno de: {tipos_str}"
            )
            raise InvalidActionError(msg)


class AttackRestrictionValidator:
    """Valida restricciones de ataque."""

    @staticmethod
    def validate_not_first_turns(
        game: "Game | IGameProtocol",
        error_message: str | None = None,
    ) -> None:
        """Valida que no sea uno de los primeros turnos donde no se puede atacar.

        Args:
            game: Instancia del juego.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si es uno de los primeros turnos.

        """
        turno_actual = game.turno_actual()
        if isinstance(turno_actual, PrimerTurno | SegundoTurno):
            msg = error_message or (
                f"No se puede atacar en los primeros "
                f"{FIRST_TURNS_NO_ATTACK} turnos. "
                "Debe esperar al tercer turno."
            )
            raise InvalidActionError(msg)
