"""Tests para TurnValidator."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.exceptions import GameNotStartedError, NotPlayerTurnError
from pyteg.server.juego.validators import TurnValidator


class TurnValidatorTests(unittest.TestCase):
    """Validación de turno comparando userid (int) del cliente con el turno."""

    def test_none_game_raises_game_not_started(self) -> None:
        """Sin partida activa debe fallar con GameNotStartedError."""
        client = MagicMock()
        with self.assertRaises(GameNotStartedError):
            TurnValidator.validate_turn(client, None)

    def test_matching_userid_passes(self) -> None:
        """Si el userid en turno coincide con el cliente, no debe lanzar."""
        client = MagicMock()
        client.userid.return_value = 42

        turno = MagicMock()
        turno.jugador_actual.return_value = 42

        game = MagicMock()
        game.turno_actual.return_value = turno

        TurnValidator.validate_turn(client, game)

    def test_different_userid_raises(self) -> None:
        """Si actúa otro jugador, debe lanzar NotPlayerTurnError."""
        client = MagicMock()
        client.userid.return_value = 1

        turno = MagicMock()
        turno.jugador_actual.return_value = 2

        game = MagicMock()
        game.turno_actual.return_value = turno

        with self.assertRaises(NotPlayerTurnError):
            TurnValidator.validate_turn(client, game)

    def test_zero_turn_player_raises(self) -> None:
        """El userid 0 en turno se trata como sin turno válido."""
        client = MagicMock()
        client.userid.return_value = 1

        turno = MagicMock()
        turno.jugador_actual.return_value = 0

        game = MagicMock()
        game.turno_actual.return_value = turno

        with self.assertRaises(NotPlayerTurnError):
            TurnValidator.validate_turn(client, game)


if __name__ == "__main__":
    unittest.main()
