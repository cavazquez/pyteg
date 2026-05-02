"""Tests para CountryOwnershipValidator (dueño en mapa = userid int)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.exceptions import CountryNotOwnedError, InvalidActionError
from pyteg.server.juego.validators import CountryOwnershipValidator


class CountryOwnershipValidatorTests(unittest.TestCase):
    """La propiedad en el mapa coincide con client.userid()."""

    def test_validate_ownership_matches_userid(self) -> None:
        """Dueño en mapa == userid del cliente → OK."""
        client = MagicMock()
        client.userid.return_value = 99
        mapa = MagicMock()
        mapa.ocupado_por.return_value = 99

        CountryOwnershipValidator.validate_ownership(client, mapa, "Uruguay")

    def test_validate_ownership_mismatch_userid(self) -> None:
        """Dueño distinto al userid del cliente → error."""
        client = MagicMock()
        client.userid.return_value = 99
        mapa = MagicMock()
        mapa.ocupado_por.return_value = 100

        with self.assertRaises(CountryNotOwnedError):
            CountryOwnershipValidator.validate_ownership(client, mapa, "Brasil")

    def test_validate_not_own_country_same_owner_raises(self) -> None:
        """No se puede atacar si el ocupante es el mismo jugador (por userid)."""
        client = MagicMock()
        client.userid.return_value = 99
        mapa = MagicMock()
        mapa.ocupado_por.return_value = 99

        with self.assertRaises(InvalidActionError):
            CountryOwnershipValidator.validate_not_own_country(client, mapa, "X")


if __name__ == "__main__":
    unittest.main()
