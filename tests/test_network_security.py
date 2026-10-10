"""Identidades, admisión TLS y rechazo de suplantaciones y repeticiones."""

# ruff: noqa: D102, SLF001

from __future__ import annotations

import contextlib
import socket
import ssl
import unittest
from copy import deepcopy
from dataclasses import replace
from unittest.mock import MagicMock, patch

from pyteg.network.game_security import GameChannel, GameSecurity, signed_command
from pyteg.network.identity import Identity, engine_token, verify
from pyteg.network.peer_runtime import PeerNode
from pyteg.network.peer_transport import PeerPort, exchange
from pyteg.network.security import (
    Invitation,
    RoomAccess,
    TlsCredentials,
    authenticate,
    challenge,
    connect_tls,
    proof,
)
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.server.conexion.cliente import Client


class IdentitySecurityTests(unittest.TestCase):
    """Las firmas se vinculan con autor, contenido, sala y canal."""

    def setUp(self) -> None:
        self.identity = Identity()
        self.other = Identity()
        self.access = RoomAccess()

    def test_private_key_restores_only_its_own_identity(self) -> None:
        restored = Identity.restore(self.identity.export_private())
        self.assertEqual(restored.public_key, self.identity.public_key)
        value = {"action": "reforzar", "amount": 2}
        signature = self.identity.sign(value)
        self.assertTrue(verify(restored.public_key, value, signature))
        self.assertFalse(verify(self.other.public_key, value, signature))
        self.assertFalse(verify(restored.public_key, {**value, "amount": 3}, signature))

    def test_handshake_proof_cannot_be_replayed_or_altered(self) -> None:
        greeting = challenge()
        request = {"message": "status", "session_id": self.access.session_id}
        packet = proof(self.identity, greeting, request)
        self.assertEqual(
            authenticate(greeting, packet), (request, self.identity.public_key)
        )
        for damaged in (
            {**packet, "public_key": self.other.public_key},
            {**packet, "request": {**request, "message": "vote"}},
            proof(self.identity, greeting, {"_sender_key": self.other.public_key}),
        ):
            with (
                self.subTest(packet_fields=set(damaged)),
                self.assertRaises(ValueError),
            ):
                authenticate(greeting, damaged)
        with self.assertRaises(ValueError):
            authenticate(challenge(), packet)

    def test_invitation_round_trip_and_strict_fields(self) -> None:
        invitation = self.access.invitation(
            "peer", "127.0.0.1", 12345, self.identity, "revancha"
        )
        self.assertEqual(Invitation.parse(invitation.encode()), invitation)
        self.assertNotIn(invitation.token, repr(invitation))
        self.assertNotIn(self.identity.export_private(), invitation.encode())
        for invalid in (
            invitation.encode() + "&v=1",
            invitation.encode() + "&unknown=1",
            invitation.encode() + "#fragment",
            invitation.encode().replace("pyteg://", "http://"),
        ):
            with (
                self.subTest(case=invalid.split("?", 1)[0]),
                self.assertRaises(ValueError),
            ):
                Invitation.parse(invalid)

    def test_signed_command_rejects_replay_and_other_domains(self) -> None:
        nonce = challenge()["nonce"]
        command = {"mensaje": "chat", "msg": "Hola"}
        packet = signed_command(
            self.identity, self.access.session_id, nonce, 1, command
        )
        channel = GameChannel(self.identity.public_key, self.access.session_id, nonce)
        self.assertEqual(channel.unwrap(packet), command)
        with self.assertRaises(ValueError):
            channel.unwrap(packet)
        for wrong in (
            GameChannel(self.other.public_key, self.access.session_id, nonce),
            GameChannel(self.identity.public_key, RoomAccess().session_id, nonce),
            GameChannel(
                self.identity.public_key, self.access.session_id, challenge()["nonce"]
            ),
        ):
            with self.assertRaises(ValueError):
                wrong.unwrap(packet)
            self.assertEqual(wrong.sequence, 0)
        damaged = deepcopy(packet)
        damaged["command"]["msg"] = "Alterado"
        with self.assertRaises(ValueError):
            GameChannel(self.identity.public_key, self.access.session_id, nonce).unwrap(
                damaged
            )

    def test_admission_and_reconnection_require_different_credentials(self) -> None:
        security = GameSecurity(
            TlsCredentials(self.identity),
            self.access,
            lambda: {1: self.identity.public_key},
        )
        request = {
            "message": "connect",
            "session_id": self.access.session_id,
            "invite": self.access.token,
            "user_id": None,
        }
        security._authorize(request, self.other.public_key)
        with self.assertRaises(ValueError):
            security._authorize({**request, "invite": "wrong"}, self.other.public_key)
        reconnect = {**request, "user_id": 1, "invite": ""}
        security._authorize(reconnect, self.identity.public_key)
        with self.assertRaises(ValueError):
            security._authorize(reconnect, self.other.public_key)
        with self.assertRaises(ValueError):
            security._authorize(
                {**reconnect, "invite": engine_token(self.identity.public_key)},
                self.other.public_key,
            )

    def test_public_engine_token_cannot_impersonate_network_or_local_player(
        self,
    ) -> None:
        session = AsyncGame.create("classic", ["Uno", "Dos"])
        self.addCleanup(session.close)
        server = session.server
        historical = server.dame_clientes()[0]
        historical.set_network_key(self.identity.public_key)
        incoming = Client(
            99,
            MagicMock(network_public_key=self.other.public_key),
            server,
            "Intruso",
            soy_admin=False,
        )
        self.assertFalse(
            server.reconectar_cliente(
                incoming, historical.userid(), historical.reconnect_token()
            )
        )
        local = server.dame_clientes()[1]
        self.assertFalse(
            server.reconectar_cliente(incoming, local.userid(), local.reconnect_token())
        )


class TransportSecurityTests(unittest.TestCase):
    """Conexiones reales con claves individuales y certificados fijados."""

    def test_tls_pin_and_fresh_client_proof_precede_the_handler(self) -> None:
        server, client = Identity(), Identity()
        received: list[str] = []

        def handler(request: dict[str, object], _host: str) -> dict[str, object]:
            received.append(str(request["_sender_key"]))
            return {"accepted": True}

        port = PeerPort(handler, identity=server)
        self.addCleanup(port.close)
        port.start()
        address = "127.0.0.1", port.port
        with connect_tls(address, server.public_key, 2) as secure:
            self.assertIsInstance(secure, ssl.SSLSocket)
            self.assertEqual(secure.version(), "TLSv1.3")
        reply = exchange(
            address,
            {"message": "status"},
            identity=client,
            expected_key=server.public_key,
        )
        self.assertTrue(reply["accepted"])
        self.assertEqual(received, [client.public_key])
        with self.assertRaises(ValueError):
            exchange(
                address,
                {"message": "status"},
                identity=client,
                expected_key=Identity().public_key,
            )
        self.assertEqual(received, [client.public_key])
        with socket.create_connection(address, timeout=1) as plaintext:
            plaintext.sendall(b'{"message":"status"}\0')
            with contextlib.suppress(ConnectionResetError):
                self.assertIn(plaintext.recv(4096)[:1], (b"", b"\x15"))
        self.assertEqual(received, [client.public_key])

    def test_peer_rejects_wrong_admission_identity_and_forged_certificate(self) -> None:
        with patch.object(PeerNode, "start_maintenance"):
            creator = PeerNode.create("classic", "Uno", "classic")
            self.addCleanup(creator.close)
            invitation = creator.invitation("127.0.0.1")
            address = invitation.host, invitation.port
            with self.assertRaises(ValueError):
                PeerNode.join(
                    address,
                    "Intruso",
                    invitation=replace(invitation, token=RoomAccess().token),
                )
            peer = PeerNode.join(address, "Dos", invitation=invitation)
            self.addCleanup(peer.close)
            with self.assertRaises(ValueError):
                PeerNode.join(
                    address,
                    "Intruso",
                    invitation=invitation,
                    identity=(peer.user_id, Identity().export_private()),
                )
            creator.submit({"mensaje": "chat", "msg": "Confirmado"})
            damaged = creator.document
            damaged["certificate"]["votes"][0]["signature"] = "00" * 64
            with self.assertRaises(ValueError):
                creator._validate_document(damaged)
            for node in (creator, peer):
                self.assertNotIn(node.identity.export_private(), str(creator.document))
            self.assertEqual(
                peer.draft()["payload"]["peer"]["private_key"],
                peer.identity.export_private(),
            )


if __name__ == "__main__":
    unittest.main()
