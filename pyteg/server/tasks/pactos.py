# ruff: noqa: DOC201, DOC501, D107, EM101, TRY003

"""Comandos públicos para proponer, aceptar y romper pactos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.exceptions import InvalidActionError, MissingFieldError
from pyteg.server.juego.validators import (
    GameStateValidator,
    PhaseValidator,
    TurnValidator,
)
from pyteg.server.tasks.base import IServerTask
from pyteg.server.tasks.types import (
    AceptarPactoTaskData,
    ProponerPactoTaskData,
    RomperPactoTaskData,
)

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


def _player_exists(context: GameContext, player_id: int) -> bool:
    """Comprueba que el invitado siga perteneciendo a la partida."""
    return any(
        int(client.userid()) == int(player_id) for client in context.dame_clientes()
    )


def _require_revancha(context: GameContext) -> None:
    """Limita las reglas de pactos a la edición que las define."""
    if context.reglas().theme != "revancha":
        raise InvalidActionError("Los pactos sólo están disponibles en Revancha")


class ServerTaskProponerPacto(IServerTask[ProponerPactoTaskData]):
    """Crea una propuesta pendiente visible para todos."""

    def __init__(self, data: ProponerPactoTaskData) -> None:
        super().__init__(data)
        self._tipo = data.get("tipo")
        self._jugador_objetivo = data.get("jugador_objetivo")
        self._paises = tuple(data.get("paises", []))
        self._continentes = tuple(data.get("continentes", []))
        self._pais_objetivo = data.get("pais_objetivo")
        self._duracion = data.get("duracion", 1)
        self._action_name = "proponer_pacto"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        if self._tipo is None:
            raise MissingFieldError("tipo")
        if self._jugador_objetivo is None:
            raise MissingFieldError("jugador_objetivo")
        GameStateValidator.validate_game_started(context.game)
        PhaseValidator.validate_command(context.game, "proponer_pacto")
        _require_revancha(context)
        TurnValidator.validate_turn(client, context.game)
        if int(self._jugador_objetivo) == int(client.userid()):
            raise InvalidActionError("No puedes pactar contigo mismo")
        if not _player_exists(context, int(self._jugador_objetivo)):
            raise InvalidActionError("El jugador objetivo no está en la partida")
        if context.game is None:
            return
        context.game.pactos().proponer(
            proponente=int(client.userid()),
            jugador_objetivo=int(self._jugador_objetivo),
            tipo=str(self._tipo),
            ronda=context.game.num_ronda(),
            paises=self._paises,
            continentes=self._continentes,
            pais_objetivo=self._pais_objetivo,
            duracion=self._duracion,
        )
        context.enviar_snapshot()


class ServerTaskAceptarPacto(IServerTask[AceptarPactoTaskData]):
    """Activa una propuesta sólo desde el jugador invitado."""

    def __init__(self, data: AceptarPactoTaskData) -> None:
        super().__init__(data)
        self._pacto_id = data.get("pacto_id")
        self._action_name = "aceptar_pacto"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        if self._pacto_id is None:
            raise MissingFieldError("pacto_id")
        GameStateValidator.validate_game_started(context.game)
        PhaseValidator.validate_command(context.game, "aceptar_pacto")
        _require_revancha(context)
        TurnValidator.validate_turn(client, context.game)
        if context.game is None:
            return
        context.game.pactos().aceptar(
            self._pacto_id,
            int(client.userid()),
            context.game.num_ronda(),
        )
        context.enviar_snapshot()


class ServerTaskRomperPacto(IServerTask[RomperPactoTaskData]):
    """Anuncia una ruptura con el plazo reglamentario."""

    def __init__(self, data: RomperPactoTaskData) -> None:
        super().__init__(data)
        self._pacto_id = data.get("pacto_id")
        self._action_name = "romper_pacto"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        if self._pacto_id is None:
            raise MissingFieldError("pacto_id")
        GameStateValidator.validate_game_started(context.game)
        PhaseValidator.validate_command(context.game, "romper_pacto")
        _require_revancha(context)
        TurnValidator.validate_turn(client, context.game)
        if context.game is None:
            return
        context.game.pactos().romper(
            self._pacto_id,
            int(client.userid()),
            context.game.num_ronda(),
        )
        context.enviar_snapshot()


__all__ = [
    "ServerTaskAceptarPacto",
    "ServerTaskProponerPacto",
    "ServerTaskRomperPacto",
]
