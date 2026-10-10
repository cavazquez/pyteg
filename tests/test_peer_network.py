"""Acuerdos entre pares: persistencia, validación y TCP simétrico real."""

# ruff: noqa: D102, SLF001

from __future__ import annotations

import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from typing import Any
from unittest.mock import patch

from pyteg.network.peer_consensus import ConsensusSlot, ballot, previously_accepted
from pyteg.network.peer_runtime import PeerNode
from pyteg.network.peer_state import agreement
from pyteg.persistence.archive import MemoryRepository


class ConsensusSlotTests(unittest.TestCase):
    """Una promesa persiste y conserva el mayor valor aceptado."""

    def test_rejects_older_and_conflicting_votes_after_restore(self) -> None:
        slot = ConsensusSlot()
        self.assertIsNotNone(slot.prepare((2, 1)))
        self.assertTrue(slot.accept((2, 1), {"state": "a"}))
        restored = ConsensusSlot.restore(slot.snapshot())
        self.assertIsNone(restored.prepare((1, 2)))
        self.assertFalse(restored.accept((2, 1), {"state": "b"}))
        reply = restored.prepare((3, 2))
        self.assertIsNotNone(reply)
        self.assertEqual(previously_accepted([reply or {}]), {"state": "a"})

    def test_joint_membership_requires_both_majorities(self) -> None:
        old = [{"userid": uid} for uid in (1, 2, 3, 4)]
        new = [{"userid": uid} for uid in (2, 3, 4)]
        self.assertFalse(agreement(old, new, [2, 3]))
        self.assertTrue(agreement(old, new, [2, 3, 4]))
        self.assertFalse(agreement(old, new, [2, 2, 2]))

    def test_invalid_ballots_and_slots_are_rejected(self) -> None:
        for value in ([True, 1], [-1, 1], [1, 0], [2**64, 1], [1]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ballot(value)
        state = ConsensusSlot().snapshot()
        state["accepted_ballot"] = [3, 2]
        with self.assertRaises(ValueError):
            ConsensusSlot.restore(state)


class PeerNetworkTests(unittest.TestCase):
    """Cada caso usa listeners TCP propios y motores reales sin reloj autónomo."""

    def setUp(self) -> None:
        # Los casos controlan el reloj y la detección de caídas explícitamente.
        self.maintenance = patch.object(PeerNode, "start_maintenance")
        self.maintenance.start()
        self.addCleanup(self.maintenance.stop)
        self.nodes: list[PeerNode] = []
        self.addCleanup(self.close_nodes)

    def close_nodes(self) -> None:
        for node in self.nodes:
            node.close()

    def room(
        self, theme: str = "classic", profile: str = "classic", players: int = 4
    ) -> list[PeerNode]:
        creator = PeerNode.create(theme, "Uno", profile)
        self.nodes.append(creator)
        for index in range(1, players):
            node = PeerNode.join(
                ("127.0.0.1", self.nodes[-1].port),
                f"Jugador {index + 1}",
                invitation=self.nodes[-1].invitation("127.0.0.1"),
            )
            self.nodes.append(node)
        return self.nodes

    def same_state(self, nodes: list[PeerNode]) -> None:
        # Espera sólo la difusión en curso: no incorpora otra transición.
        for node in nodes:
            for member in node.document["state"]["members"]:
                if member["userid"] == node.user_id or member["userid"] not in {
                    peer.user_id for peer in nodes
                }:
                    continue
                response = node._request(member, "status", {})
                node._install_document(response["document"])
        self.assertEqual(len({node.document["hash"] for node in nodes}), 1)

    def start_game(self, node: PeerNode) -> None:
        configured = node.submit({
            "mensaje": "empezar",
            "segundos": 60,
            "paises_para_victoria": 0,
        })
        started = node.submit({"mensaje": "empezar_partida"})
        self.assertTrue(configured and configured["accepted"])
        self.assertTrue(started and started["accepted"])

    def test_four_peers_validate_both_maps_and_rule_profiles(self) -> None:
        for theme, profile in (("classic", "revancha"), ("revancha", "classic")):
            with self.subTest(theme=theme, profile=profile):
                nodes = self.room(theme, profile)
                self.start_game(nodes[0])
                self.same_state(nodes)
                self.assertEqual(nodes[0].document["state"]["clock"]["remaining"], 60)
                self.close_nodes()
                self.nodes.clear()

    def test_join_waits_for_membership_consensus(self) -> None:
        creator = self.room(players=1)[0]
        propose = creator.propose

        def delayed_proposal(operation: dict[str, Any]) -> dict[str, Any] | None:
            # La confirmación puede necesitar varias rondas de votos y disco.
            time.sleep(3.2)
            return propose(operation)

        with patch.object(creator, "propose", side_effect=delayed_proposal):
            joined = PeerNode.join(
                ("127.0.0.1", creator.port),
                "Dos",
                invitation=creator.invitation("127.0.0.1"),
            )
        self.nodes.append(joined)
        self.same_state(self.nodes)
        self.assertEqual(joined.user_id, 2)

    def test_creator_can_disappear_and_any_other_peer_commits(self) -> None:
        nodes = self.room()
        self.start_game(nodes[0])
        nodes[0].close()
        for node in nodes[1:]:
            node._seen[1] = 0
        nodes[2].propose({"kind": "leave", "actor": 3, "target": 1})
        self.same_state(nodes[1:])
        result = nodes[3].submit({"mensaje": "chat", "msg": "Seguimos"})
        self.assertTrue(result and result["accepted"])
        self.same_state(nodes[1:])

    def test_minority_cannot_confirm_an_action_or_decrement_clock(self) -> None:
        nodes = self.room()
        self.start_game(nodes[0])
        nodes[2].close()
        nodes[3].close()
        before = nodes[0].document
        with self.assertRaisesRegex(ValueError, "mayoría"):
            nodes[0].submit({"mensaje": "chat", "msg": "sin mayoría"})
        self.assertEqual(nodes[0].document, before)
        with self.assertRaisesRegex(ValueError, "mayoría"):
            nodes[1].propose({"kind": "tick", "actor": 2})
        self.assertEqual(nodes[1].document["state"]["clock"], before["state"]["clock"])

    def test_failed_storage_does_not_publish_a_promise(self) -> None:
        node = self.room(players=1)[0]
        before = node._slot.snapshot()
        request = node._packet(
            "prepare", {"before": node.document["hash"], "ballot": [9, 1]}
        )
        request["_sender_key"] = node.identity.public_key
        with (
            patch.object(node._repository, "save", side_effect=OSError("disco lleno")),
            self.assertRaises(OSError),
        ):
            node._handle(request, "127.0.0.1")
        self.assertEqual(node._slot.snapshot(), before)

    def test_simultaneous_proposers_keep_a_single_history(self) -> None:
        nodes = self.room()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    node.submit, {"mensaje": "chat", "msg": str(node.user_id)}
                )
                for node in nodes[1:3]
            ]
            for future in futures:
                try:
                    result = future.result(timeout=15)
                except ValueError:
                    # La interfaz permite reintentar una propuesta que perdió
                    # la carrera. El acuerdo no puede confirmar dos ramas.
                    continue
                self.assertTrue(result and result["accepted"])
        self.same_state(nodes)

    def test_failed_commit_keeps_the_accepted_value_for_recovery(self) -> None:
        node = self.room(players=1)[0]
        before = node.document
        save = node._repository.save
        calls = 0

        def fail_commit(archive: dict[str, object]) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:  # noqa: PLR2004 -- promesa, aceptación y commit.
                msg = "fallo al guardar commit"
                raise OSError(msg)
            save(archive)

        with (
            patch.object(node._repository, "save", side_effect=fail_commit),
            self.assertRaises(OSError),
        ):
            node.submit({"mensaje": "empezar", "segundos": 77})
        self.assertEqual(node.document, before)
        self.assertIsNotNone(node._slot.accepted_value)
        node.submit({"mensaje": "chat", "msg": "recuperar"})
        self.assertEqual(
            node.game.server.public_snapshot()["configuracion"]["segundos_por_turno"],
            77,
        )

    def test_clock_tick_and_expiration_are_shared_transitions(self) -> None:
        nodes = self.room(players=2)
        nodes[0].submit({"mensaje": "empezar", "segundos": 1})
        nodes[0].submit({"mensaje": "empezar_partida"})
        before = nodes[0].document["state"]["clock"]["marker"]
        for node in nodes:
            node._last_tick = 0
        nodes[1].propose({"kind": "tick", "actor": 2})
        self.same_state(nodes)
        self.assertNotEqual(nodes[0].document["state"]["clock"]["marker"], before)
        self.assertEqual(nodes[0].document["state"]["clock"]["remaining"], 1)

    def test_new_room_does_not_restore_an_unrelated_repository(self) -> None:
        repository = MemoryRepository()
        old = PeerNode.create("classic", "Anterior", "classic")
        old_peer = PeerNode.join(
            ("127.0.0.1", old.port),
            "Dos",
            repository=repository,
            invitation=old.invitation("127.0.0.1"),
        )
        self.nodes.extend((old, old_peer))
        creator = PeerNode.create("revancha", "Nueva", "revancha")
        self.nodes.append(creator)
        joined = PeerNode.join(
            ("127.0.0.1", creator.port),
            "Dos",
            repository=repository,
            invitation=creator.invitation("127.0.0.1"),
        )
        self.nodes.append(joined)
        self.assertEqual(
            joined.document["state"]["session_id"],
            creator.document["state"]["session_id"],
        )
        self.assertNotEqual(
            joined.document["state"]["session_id"], old.document["state"]["session_id"]
        )

    def test_pending_vote_is_adopted_after_proposer_disappears(self) -> None:
        nodes = self.room()
        with (
            patch.object(
                nodes[0],
                "_install_document",
                side_effect=OSError("cayó antes del commit"),
            ),
            self.assertRaises(OSError),
        ):
            nodes[0].submit({"mensaje": "empezar", "segundos": 37})
        self.assertTrue(any(node._slot.accepted_value for node in nodes))
        nodes[0].close()
        result = nodes[2].submit({"mensaje": "chat", "msg": "recuperar voto"})
        self.assertTrue(result and result["accepted"])
        self.same_state(nodes[1:])
        self.assertEqual(
            nodes[1].game.server.public_snapshot()["configuracion"][
                "segundos_por_turno"
            ],
            37,
        )

    def test_current_identity_reconnects_through_a_different_peer(self) -> None:
        nodes = self.room()
        self.start_game(nodes[0])
        saved = nodes[1].draft()
        nodes[1].close()
        propose = nodes[3].propose

        def delayed_proposal(operation: dict[str, Any]) -> dict[str, Any] | None:
            time.sleep(3.2)
            return propose(operation)

        with patch.object(nodes[3], "propose", side_effect=delayed_proposal):
            replacement = PeerNode.join(
                ("127.0.0.1", nodes[3].port),
                "Jugador 2",
                identity=(2, saved["payload"]["peer"]["private_key"]),
                saved_archive=saved,
                invitation=nodes[3].invitation("127.0.0.1"),
            )
        nodes[1] = replacement
        self.same_state(nodes)
        self.assertEqual(replacement.user_id, 2)
        self.assertEqual(
            replacement.identity.export_private(),
            saved["payload"]["peer"]["private_key"],
        )

    def test_saved_promises_and_duplicate_commands_survive_restart(self) -> None:
        repository = MemoryRepository()
        node = PeerNode.create("classic", "Uno", "classic", repository=repository)
        self.nodes.append(node)
        command = {
            "mensaje": "empezar",
            "segundos": 34,
            "command_id": "persistent-command",
        }
        first = node.submit(command)
        node._handle(
            {
                **node._packet(
                    "prepare", {"before": node.document["hash"], "ballot": [2**62, 1]}
                ),
                "_sender_key": node.identity.public_key,
            },
            "127.0.0.1",
        )
        saved = node.draft()
        node.close()
        reopened = PeerNode.open(saved, repository=repository)
        self.nodes[0] = reopened
        self.assertEqual(reopened._slot.promised, (2**62, 1))
        repeated = reopened.submit(command)
        self.assertEqual(repeated, first)
        self.assertEqual(
            reopened.game.server.public_snapshot()["revision"],
            first["revision"] if first else 0,
        )

    def test_altered_state_and_unauthenticated_messages_are_rejected(self) -> None:
        node = self.room(players=1)[0]
        node.submit({"mensaje": "empezar"})
        damaged = deepcopy(node.document)
        damaged["state"]["clock"] = {"marker": [1, 0, 1], "remaining": 9000}
        with self.assertRaises(ValueError):
            node._install_document(damaged)
        with self.assertRaises(ValueError):
            node._handle(
                {
                    "message": "status",
                    "session": node.document["state"]["session_id"],
                    "actor": 1,
                    "body": {},
                    "signature": "wrong",
                },
                "127.0.0.1",
            )


if __name__ == "__main__":
    unittest.main()
