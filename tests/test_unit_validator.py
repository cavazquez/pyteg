"""Tests para las cantidades usadas al mover unidades."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.exceptions import InvalidActionError
from pyteg.server.juego.validators import UnitValidator


class UnitValidatorTests(unittest.TestCase):
    """El validador no permite cantidades que puedan corromper el mapa."""

    def test_move_quantity_must_be_a_positive_integer(self) -> None:
        """Cero, negativos, bool, fracciones y otros tipos fallan antes del mapa."""
        mapa = MagicMock()
        invalid_amounts: tuple[object, ...] = (0, -1, True, 1.5, "1", None)

        for amount in invalid_amounts:
            with self.subTest(amount=amount), self.assertRaises(InvalidActionError):
                UnitValidator.validate_sufficient_units_to_move(mapa, "Origen", amount)

        mapa.cantidad_unidades.assert_not_called()

    def test_move_quantity_leaves_at_least_one_unit_in_origin(self) -> None:
        """Una cantidad válida se acepta sólo si no vacía el país de origen."""
        mapa = MagicMock()
        mapa.cantidad_unidades.return_value = 3

        UnitValidator.validate_sufficient_units_to_move(mapa, "Origen", 2)

        with self.assertRaises(InvalidActionError):
            UnitValidator.validate_sufficient_units_to_move(mapa, "Origen", 3)


if __name__ == "__main__":
    unittest.main()
