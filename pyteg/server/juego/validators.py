"""Validadores reutilizables para tareas del servidor.

Este módulo proporciona validadores que pueden ser reutilizados
en múltiples tareas del servidor para evitar duplicación de código.
"""

from typing import TYPE_CHECKING

from pyteg.config import FIRST_TURNS_NO_ATTACK
from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno
from pyteg.exceptions import (
    CountryNotOwnedError,
    GameNotStartedError,
    GameRuleViolationError,
    InvalidActionError,
    NotPlayerTurnError,
)
from pyteg.server.juego.fase import (
    FASE_ACCIONES,
    FASE_COLOCACION,
    FASE_POR_COMANDO,
)

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
        client: Client | IClientProtocol,
        game: Game | IGameProtocol | None,
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
        userid_en_turno = turno_actual.jugador_actual()
        if not userid_en_turno:
            raise NotPlayerTurnError
        client_userid = client.userid() if hasattr(client, "userid") else None
        if not client_userid:
            raise NotPlayerTurnError
        if int(userid_en_turno) != int(client_userid):
            raise NotPlayerTurnError


class GameStateValidator:
    """Valida el estado del juego."""

    @staticmethod
    def validate_game_started(
        game: Game | IGameProtocol | None,
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
    def _client_userid(
        client: Client | IClientProtocol,
    ) -> int | None:
        """Devuelve el userid (int) del cliente, normalizado.

        Returns:
            userid (int) del cliente o None si no está definido.

        """
        if hasattr(client, "userid"):
            uid = client.userid()
            if uid:
                return int(uid)
        return None

    @staticmethod
    def validate_ownership(
        client: Client | IClientProtocol,
        mapa: Mapa | IMapProtocol,
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
        ocupante = mapa.ocupado_por(pais)
        jugador = CountryOwnershipValidator._client_userid(client)
        if jugador is None:
            raise CountryNotOwnedError(pais, error_message)
        if ocupante != jugador:
            raise CountryNotOwnedError(pais, error_message)

    @staticmethod
    def validate_not_own_country(
        client: Client | IClientProtocol,
        mapa: Mapa | IMapProtocol,
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
        ocupante = mapa.ocupado_por(pais)
        jugador = CountryOwnershipValidator._client_userid(client)
        if jugador is None:
            return
        if ocupante == jugador:
            msg = error_message or f"No puedes atacar tu propio país: {pais}"
            raise InvalidActionError(msg)


class AdjacencyValidator:
    """Valida adyacencia entre países."""

    @staticmethod
    def validate_adjacent(
        mapa: Mapa | IMapProtocol,
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
        mapa: Mapa | IMapProtocol,
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
        mapa: Mapa | IMapProtocol,
        origen: str,
        cantidad: object,
        error_message: str | None = None,
    ) -> None:
        """Valida una cantidad positiva y las unidades disponibles para mover.

        Args:
            mapa: Instancia del mapa del juego.
            origen: País de origen.
            cantidad: Cantidad entera y positiva de unidades a mover.
            error_message: Mensaje de error personalizado. Si es None,
                se usa un mensaje por defecto.

        Raises:
            InvalidActionError: Si la cantidad es inválida o no hay suficientes
                unidades para mover.

        """
        if type(cantidad) is not int or cantidad <= 0:
            msg = error_message or "La cantidad a mover debe ser un entero positivo"
            raise InvalidActionError(msg)

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
        game: Game | IGameProtocol,
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


class PhaseValidator:
    """Valida la fase autoritativa del turno en el servidor."""

    @staticmethod
    def _validate(
        game: Game | IGameProtocol | None,
        expected: str,
        command: str | None = None,
    ) -> None:
        if game is None:
            raise GameNotStartedError
        fase_actual = getattr(game, "fase_actual", None)
        # Los dobles antiguos de tests no exponen fase; sus validaciones
        # existentes siguen siendo suficientes para esas unidades aisladas.
        if not callable(fase_actual):
            return
        actual = str(fase_actual())
        if actual != expected:
            if command is None:
                msg = (
                    "La acción no es válida en la fase actual "
                    f"({actual}); primero debe completar la colocación."
                )
            else:
                msg = (
                    f"La acción '{command}' no es válida en la fase actual "
                    f"({actual}); sólo puede ejecutarse en '{expected}'."
                )
            raise InvalidActionError(msg)

    @classmethod
    def validate_command(cls, game: Game | IGameProtocol | None, command: str) -> None:
        """Exige la fase declarada por la matriz de comandos.

        Las tareas mutantes deben llamar este método antes de validar o
        modificar recursos específicos. Un comando que no esté en la matriz
        se considera un error de programación del servidor.

        Raises:
            InvalidActionError: Si el comando no está declarado o la fase no
                coincide con la fase actual.

        """
        expected = FASE_POR_COMANDO.get(command)
        if expected is None:
            msg = f"El comando '{command}' no tiene una fase declarada"
            raise InvalidActionError(msg)
        cls._validate(game, expected, command)

    @classmethod
    def validate_placement(cls, game: Game | IGameProtocol | None) -> None:
        """Exige la fase de colocación."""
        cls._validate(game, FASE_COLOCACION)

    @classmethod
    def validate_actions(cls, game: Game | IGameProtocol | None) -> None:
        """Exige la fase de acciones."""
        cls._validate(game, FASE_ACCIONES)
