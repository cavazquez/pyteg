"""La prueba de caída debe terminar al anfitrión confirmado por las réplicas."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from pyteg.client.app import Client
from scripts.smoke_host_migration import (
    _confirmed_host,  # noqa: PLC2701 -- regresión del smoke de migración.
)

if TYPE_CHECKING:
    from pyteg.gui import Gui


class HostSmokeOwnerTests(unittest.TestCase):
    """Un motor de candidato no demuestra que su jugador sea el anfitrión."""

    @staticmethod
    def _window(user_id: int, epoch: int) -> Any:
        client = Client()
        client.set_userid(user_id)
        return SimpleNamespace(
            client=client,
            host_runtime=SimpleNamespace(
                server=SimpleNamespace(
                    host_replication=SimpleNamespace(epoch=epoch, owner_id=user_id)
                )
            ),
        )

    def test_ignores_a_candidate_before_the_confirmed_owner(self) -> None:
        """Elige al dueño del checkpoint aunque otro candidato tenga un motor."""
        candidate = self._window(3, 1)
        owner = self._window(2, 1)
        with patch(
            "scripts.smoke_host_migration._checkpoint",
            return_value={"epoch": 1, "owner_id": 2},
        ):
            self.assertIs(_confirmed_host(cast("list[Gui]", [candidate, owner])), owner)

    def test_waits_until_replica_authorities_agree(self) -> None:
        """No termina un motor mientras las réplicas indican dueños distintos."""
        windows = [self._window(2, 1), self._window(3, 1)]
        with patch(
            "scripts.smoke_host_migration._checkpoint",
            side_effect=lambda window: {
                "epoch": 1,
                "owner_id": window.client.userid(),
            },
        ):
            self.assertIsNone(_confirmed_host(cast("list[Gui]", windows)))

    def test_supports_epochs_skipped_by_unsuccessful_elections(self) -> None:
        """Una recuperación puede confirmar una época mayor a uno o dos."""
        owner = self._window(2, 7)
        with patch(
            "scripts.smoke_host_migration._checkpoint",
            return_value={"epoch": 7, "owner_id": 2},
        ):
            self.assertIs(_confirmed_host(cast("list[Gui]", [owner])), owner)
