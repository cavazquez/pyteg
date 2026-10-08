# ruff: noqa: SLF001
"""Estado de recuperación Qt y reactivación de las acciones del jugador."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, ClassVar, cast
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QLabel

from pyteg.client.hosting import HostSession
from pyteg.i18n import get_current_language, set_language

if TYPE_CHECKING:
    from pyteg.client.conexion.connection import ConnectionClient


class ClientHostingTests(unittest.TestCase):
    """La coordinación del anfitrión actualiza la GUI sin proyectar secretos."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        """Reutiliza la aplicación Qt de la suite."""
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        """Crea una sesión con un puerto Qt y servicios de red inertes."""
        previous = get_current_language()
        set_language("es")
        self.addCleanup(set_language, previous)
        connection = QObject()
        self.connection = cast("Any", connection)
        self.connection.endpoint = MagicMock(return_value=("127.0.0.1", 65432))
        self.connection.reconnect_to = MagicMock()
        self.connection.reset_replica_revision = MagicMock()
        self.window = SimpleNamespace(
            client=MagicMock(),
            host_runtime=None,
            network_status_label=QLabel(),
            refresh_gameplay_actions=MagicMock(),
        )
        self.window.client.userid.return_value = 2
        self.session = HostSession(cast("ConnectionClient", connection), self.window)
        self.addCleanup(self.session.stop)
        self.addCleanup(self.window.network_status_label.close)
        runtime = patch.object(self.session, "runtime", return_value=MagicMock())
        self.runtime = runtime.start().return_value
        self.addCleanup(runtime.stop)

    @staticmethod
    def _copy(sequence: int, *, recovering: bool) -> dict[str, Any]:
        return {
            "mensaje": "host_checkpoint",
            "session_id": "test-room",
            "epoch": 1,
            "sequence": sequence,
            "owner_id": 2,
            "recovering": recovering,
            "checkpoint": {"version": 1},
        }

    def test_independent_server_shows_connected_status(self) -> None:
        """El servidor separado también muestra su destino en la barra."""
        self.session.connected()
        self.assertEqual(self.window.network_status_label.text(), "Conectado")
        self.assertIn("127.0.0.1:65432", self.window.network_status_label.toolTip())
        self.assertFalse(self.session.disconnected())
        self.assertEqual(self.window.network_status_label.text(), "Desconectado")

    def test_watchdog_starts_only_after_host_migration_is_negotiated(self) -> None:
        """Una conexión normal no deja callbacks de recuperación activos."""
        self.assertFalse(self.session._watchdog.isActive())
        self.session.process({"mensaje": "hello", "capabilities": ["snapshots"]})
        self.assertFalse(self.session._watchdog.isActive())
        self.session.process({"mensaje": "hello", "capabilities": ["host_migration"]})
        self.assertTrue(self.session._watchdog.isActive())

    def test_finishing_recovery_reenables_gameplay_actions(self) -> None:
        """El final de la pausa refresca botones aunque el snapshot llegó antes."""
        self.session.enabled = True
        self.assertTrue(self.session.process(self._copy(1, recovering=True)))
        self.assertTrue(self.session.paused)
        self.window.refresh_gameplay_actions.reset_mock()
        self.assertTrue(self.session.process(self._copy(2, recovering=False)))
        self.assertFalse(self.session.paused)
        self.window.refresh_gameplay_actions.assert_called_once_with()
        self.assertEqual(self.window.network_status_label.text(), "Anfitrión")

    def test_stale_checkpoint_cannot_restart_recovery(self) -> None:
        """Una copia repetida no vuelve a pausar la GUI ni reemplaza el backup."""
        self.session.enabled = True
        self.session.process(self._copy(2, recovering=False))
        self.runtime.store_checkpoint.reset_mock()
        self.session.process(self._copy(1, recovering=True))
        self.assertFalse(self.session.paused)
        self.runtime.store_checkpoint.assert_not_called()

    def test_peer_can_redirect_to_an_already_promoted_host(self) -> None:
        """Una consulta a un suplente puede descubrir la nueva autoridad en otro."""
        self.session._envelope = {"session_id": "test-room", "epoch": 0}
        self.session._target = {"host": "192.168.1.2", "port": 12345}
        self.session._probe = MagicMock()
        self.session._probe.readAll.return_value = (
            json.dumps({
                "mensaje": "host_ready",
                "session_id": "test-room",
                "epoch": 1,
                "host": "192.168.1.3",
                "port": 65433,
            }).encode()
            + b"\0"
        )
        self.session._read_recovery_response()
        self.connection.reconnect_to.assert_called_once_with("192.168.1.3", 65433)
        self.connection.reset_replica_revision.assert_called_once_with()
