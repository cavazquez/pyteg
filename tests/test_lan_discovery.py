"""Validación y caducidad de anuncios públicos de salas LAN."""

from __future__ import annotations

import json
import socket
import threading
import time
import unittest
from typing import Any

from pyteg.network.discovery import (
    ROOM_EXPIRY_SECONDS,
    Room,
    RoomAnnouncer,
    RoomBrowser,
    RoomCatalog,
)
from pyteg.protocol import PROTOCOL_VERSION, map_hash_for_theme


class RoomCatalogTests(unittest.TestCase):
    """No confía en direcciones ni versiones anunciadas por el datagrama."""

    def setUp(self) -> None:
        """Prepara un reloj controlado y un anuncio válido."""
        self.now = 0.0
        self.catalog = RoomCatalog(lambda: self.now)
        self.data: dict[str, Any] = {
            "message": "pyteg_room",
            "protocol": PROTOCOL_VERSION,
            "session_id": "test-room",
            "epoch": 0,
            "name": "Sala de prueba",
            "theme": "revancha",
            "map_hash": map_hash_for_theme("revancha"),
            "port": 65432,
            "players": 4,
            "state": "JUGANDO",
        }

    def _send(self, **changes: Any) -> None:
        self.catalog.receive(
            json.dumps({**self.data, **changes}).encode(), "192.168.1.20"
        )

    def test_uses_real_source_and_correct_map(self) -> None:
        """La IP se obtiene del socket y no de un campo inventado."""
        self._send(host="evil.example")
        room = self.catalog.rooms()[0]
        self.assertEqual(room.host, "192.168.1.20")
        self.assertEqual(room.theme, "revancha")
        self.assertEqual(room.players, 4)

    def test_deduplicates_and_keeps_newest_authority(self) -> None:
        """Anuncios retrasados del anfitrión anterior no sustituyen al sucesor."""
        self._send(epoch=1, port=40001)
        self._send(epoch=0, port=40000)
        self.assertEqual(len(self.catalog.rooms()), 1)
        self.assertEqual(self.catalog.rooms()[0].port, 40001)

    def test_expires_rooms(self) -> None:
        """Una sala cerrada desaparece al vencer sus anuncios."""
        self._send()
        self.now = ROOM_EXPIRY_SECONDS
        self.assertEqual(self.catalog.rooms(), [])

    def test_rejects_bad_versions_maps_ports_and_types(self) -> None:
        """Los datos incorrectos no se muestran como una sala seleccionable."""
        for changes in (
            {"protocol": "old"},
            {"theme": "other"},
            {"map_hash": "wrong"},
            {"port": 0},
            {"players": True},
            {"epoch": -1},
            {"name": ""},
        ):
            with self.subTest(changes=changes):
                self._send(**changes)
                self.assertEqual(self.catalog.rooms(), [])
        self.assertIsNone(Room.parse(b"not json", "127.0.0.1"))
        self.assertIsNone(Room.parse(b" " * 2049, "127.0.0.1"))

    def test_real_udp_discovers_and_updates_a_room(self) -> None:
        """Dos sockets multicast reales comparten el anuncio sin datos privados."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reservation:
            reservation.bind(("", 0))
            port = int(reservation.getsockname()[1])
        browser = RoomBrowser(port=port)
        announcer = RoomAnnouncer(lambda: dict(self.data), port=port)
        self.addCleanup(browser.close)
        self.addCleanup(announcer.close)
        browser.start()
        announcer.start()
        deadline = time.monotonic() + 5.0
        while not browser.catalog.rooms() and time.monotonic() < deadline:
            threading.Event().wait(0.02)
        rooms = browser.catalog.rooms()
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0].theme, "revancha")
        self.assertEqual(rooms[0].port, self.data["port"])
        self.data["epoch"] = 1
        self.data["port"] = 40000
        announcer.tick()
        deadline = time.monotonic() + 5.0
        while browser.catalog.rooms()[0].epoch != 1 and time.monotonic() < deadline:
            threading.Event().wait(0.02)
        self.assertEqual(browser.catalog.rooms()[0].port, 40000)
