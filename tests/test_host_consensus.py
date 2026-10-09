# ruff: noqa: SLF001
"""Mayorías de copias, votos durables y rechazo de autoridades obsoletas."""

from __future__ import annotations

import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from pyteg.persistence.archive import FileRepository, digest
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.server.hosting.consensus import (
    LEASE_SECONDS,
    ElectionState,
    joint_majority,
    majority,
)
from pyteg.server.hosting.replication import HostReplication
from pyteg.server.hosting.runtime import HostRuntime


class ElectionTests(unittest.TestCase):
    """Cada participante sólo promete un candidato por época."""

    def test_majorities_and_joint_membership(self) -> None:
        """Dos supervivientes de cuatro no pueden cambiarse a un grupo de dos."""
        self.assertFalse(majority([1, 2, 3, 4], [1, 2, 2, 99]))
        self.assertTrue(majority([1, 2, 3, 4], [1, 2, 3]))
        self.assertTrue(majority([1], [1]))
        self.assertFalse(
            joint_majority(
                {"members": [1, 2], "previous_members": [1, 2, 3, 4]}, [1, 2]
            )
        )

    def test_lease_and_one_vote_per_term(self) -> None:
        """Se espera el lease, y el voto no cambia dentro de una época."""
        now = [0.0]
        state = ElectionState(lambda: now[0])
        state.renew(0, 1)
        self.assertFalse(state.vote(1, 2))
        now[0] = LEASE_SECONDS + 1
        self.assertTrue(state.vote(1, 2))
        self.assertTrue(state.vote(1, 2))
        self.assertFalse(state.vote(1, 3))
        self.assertFalse(state.authorize(0, 1))
        self.assertTrue(state.vote(2, 3))
        self.assertFalse(state.authorize(1, 2))

    def test_restart_retains_vote_and_waits_existing_lease(self) -> None:
        """Reiniciar un proceso no permite votar de nuevo por otro candidato."""
        state = ElectionState(lambda: 0.0)
        state.renew(3, 2)
        restarted = ElectionState(lambda: 100.0)
        restarted.restore(state.export())
        self.assertFalse(restarted.vote(4, 3))
        self.assertFalse(restarted.authorize(2, 1))


class _BackupTransport:
    """Transporte controlado para observar el orden de persistencia y ACK."""

    def __init__(self) -> None:
        self.available = {2, 3}
        self.staged = threading.Event()
        self.release = threading.Event()
        self.release.set()
        self.committed: list[dict[str, Any]] = []

    def stage_checkpoint(self, _envelope: dict[str, Any]) -> bool:
        self.staged.set()
        self.release.wait(timeout=2.0)
        return True

    def commit_checkpoint(self, envelope: dict[str, Any]) -> bool:
        self.committed.append(deepcopy(envelope))
        return True

    def exchange(self, peer: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        return {
            "userid": peer["userid"],
            "accepted": peer["userid"] in self.available,
            "digest": request["envelope"]["digest"],
        }


class DurableConfirmationTests(unittest.TestCase):
    """El cliente recibe accepted sólo después de confirmar las copias."""

    def setUp(self) -> None:
        """Asocia un motor real con un transporte de copias controlado."""
        self.received: list[dict[str, Any]] = []
        self.confirmed = threading.Event()
        self.session = AsyncGame.create(
            "classic", ["Uno", "Dos", "Tres"], receive=self._receive
        )
        self.addCleanup(self.session.close)
        self.transport = _BackupTransport()
        self.server = self.session.server
        self.server.serialized(lambda: None)
        peers = [
            {"userid": user, "host": "127.0.0.1", "port": 12345 + user}
            for user in (1, 2, 3)
        ]
        self.replication = HostReplication(
            self.server,
            lambda _data: None,
            peers=peers,
            members=[1, 2, 3],
            transport=self.transport,
        )
        self.server.host_replication = self.replication

    def _receive(self, _user_id: int, event: dict[str, Any]) -> None:
        if event.get("mensaje") == "command_result":
            self.received.append(event)
            self.confirmed.set()

    def _command(self) -> None:
        client = self.server.dame_clientes()[0]
        self.server.encolar_comando(
            client,
            {
                "mensaje": "set_username",
                "username": "Nuevo",
                "command_id": "durable-name",
            },
        )

    def test_confirmation_waits_for_durable_commit(self) -> None:
        """Preparar una copia todavía no confirma la acción al cliente."""
        self.transport.release.clear()
        self.addCleanup(self.transport.release.set)
        self._command()
        self.assertTrue(self.transport.staged.wait(timeout=2.0))
        self.assertFalse(self.confirmed.is_set())
        self.transport.release.set()
        self.assertTrue(self.confirmed.wait(timeout=2.0))
        self.assertTrue(self.received[0]["accepted"])
        checkpoint = self.transport.committed[0]["checkpoint"]
        self.assertIn("durable-name", checkpoint["players"][0]["cache"])

    def test_lost_quorum_pauses_and_retries_without_losing_result(self) -> None:
        """El resultado queda pendiente hasta que vuelve una mayoría."""
        self.transport.available.clear()
        self._command()
        self.server.serialized(lambda: None)
        self.assertTrue(self.server.host_waiting_quorum)
        self.assertFalse(self.confirmed.is_set())
        self.transport.available.add(2)
        self.server.replicar_anfitrion()
        self.assertTrue(self.confirmed.wait(timeout=2.0))
        self.assertFalse(self.server.host_waiting_quorum)


class RuntimeVoteTests(unittest.TestCase):
    """Promesas y propuestas sobreviven sin promover copias incompletas."""

    def setUp(self) -> None:
        """Crea jugadores y un memento completo."""
        self.session = AsyncGame.create("classic", ["Uno", "Dos", "Tres", "Cuatro"])
        self.addCleanup(self.session.close)
        self.checkpoint = self.session.server.capture_state()
        self.now = 0.0

    def _envelope(self, sequence: int = 1) -> dict[str, Any]:
        envelope = {
            "mensaje": "host_checkpoint",
            "session_id": "durable-room",
            "epoch": 0,
            "owner_id": 1,
            "sequence": sequence,
            "peers": [],
            "checkpoint": self.checkpoint,
            "durable": True,
            "phase": "prepared",
            "members": [1, 2, 3, 4],
            "previous_members": [1, 2, 3, 4],
            "election": [1],
        }
        envelope["digest"] = digest({
            key: value for key, value in envelope.items() if key != "phase"
        })
        return envelope

    def _runtime(self, repository: FileRepository | None = None) -> HostRuntime:
        runtime = HostRuntime(bind_host="127.0.0.1", repository=repository)
        self.addCleanup(runtime.close)
        runtime.set_identity(2)
        runtime._election = ElectionState(lambda: self.now)
        return runtime

    def test_prepared_and_insufficiently_certified_copies_are_inert(self) -> None:
        """Sólo una copia confirmada por mayoría se usa para recuperación."""
        runtime = self._runtime()
        proposal = self._envelope()
        self.assertTrue(runtime.stage_checkpoint(proposal))
        self.assertIsNone(runtime.latest_checkpoint())
        self.assertFalse(
            runtime.commit_checkpoint({
                **proposal,
                "phase": "committed",
                "certificate": [1, 2],
            })
        )
        self.assertTrue(
            runtime.commit_checkpoint({
                **proposal,
                "phase": "committed",
                "certificate": [1, 2, 3],
            })
        )
        self.assertIsNotNone(runtime.latest_checkpoint())

    def test_persisted_vote_blocks_old_authority_after_restart(self) -> None:
        """Otra instancia restaura el voto antes de contestar un RPC."""
        with TemporaryDirectory() as directory:
            repository = FileRepository(Path(directory) / "backup.pyteg")
            runtime = self._runtime(repository)
            proposal = self._envelope()
            runtime.stage_checkpoint(proposal)
            runtime.commit_checkpoint({
                **proposal,
                "phase": "committed",
                "certificate": [1, 2, 3],
            })
            self.now = LEASE_SECONDS + 1
            request = {
                "session_id": "durable-room",
                "epoch": 0,
                "user_id": 3,
                "token": self.checkpoint["players"][2]["token"],
                "sequence": 1,
                "candidate": 2,
                "term": 1,
            }
            self.assertTrue(runtime._grant_vote(request)["accepted"])
            runtime.close()
            restarted = HostRuntime(bind_host="127.0.0.1", repository=repository)
            try:
                self.assertFalse(
                    restarted._grant_vote({**request, "candidate": 3})["accepted"]
                )
                self.assertFalse(restarted.stage_checkpoint(self._envelope(2)))
                self.assertFalse(
                    restarted.store_checkpoint({
                        **self._envelope(2),
                        "phase": "committed",
                        "certificate": [1, 2, 3],
                    })
                )
            finally:
                restarted.close()

    def test_authentication_is_required_for_votes(self) -> None:
        """Un token incorrecto no puede reservar una época ni un candidato."""
        runtime = self._runtime()
        proposal = self._envelope()
        runtime.stage_checkpoint(proposal)
        runtime.commit_checkpoint({
            **proposal,
            "phase": "committed",
            "certificate": [1, 2, 3],
        })
        with self.assertRaises(ValueError):
            runtime._grant_vote({
                "session_id": "durable-room",
                "epoch": 0,
                "user_id": 2,
                "token": "wrong",
            })

    def test_gui_repository_reuses_votes_by_room_and_identity(self) -> None:
        """Una ventana nueva encuentra el voto de su identidad aunque cambie su UUID."""
        with TemporaryDirectory() as directory:
            repository = FileRepository(
                Path(directory) / "window-one.pyteg", session_scoped=True
            )
            runtime = self._runtime(repository)
            proposal = self._envelope()
            runtime.stage_checkpoint(proposal)
            runtime.commit_checkpoint({
                **proposal,
                "phase": "committed",
                "certificate": [1, 2, 3],
            })
            self.now = LEASE_SECONDS + 1
            request = {**self._request(), "candidate": 2, "term": 1, "sequence": 1}
            self.assertTrue(runtime._grant_vote(request)["accepted"])
            runtime.close()
            replacement = FileRepository(
                Path(directory) / "window-two.pyteg", session_scoped=True
            )
            restarted = HostRuntime(bind_host="127.0.0.1", repository=replacement)
            self.addCleanup(restarted.close)
            restarted.join_room("durable-room")
            restarted.set_identity(2)
            self.assertEqual(replacement.path, repository.path)
            self.assertFalse(
                restarted._grant_vote({**request, "candidate": 3})["accepted"]
            )
            self.assertFalse(restarted.can_follow(proposal))

    def test_candidate_fetches_newer_committed_backup(self) -> None:
        """Una copia retrasada se actualiza antes de pedir votos."""
        runtime = self._runtime()
        old = self._envelope()
        runtime.stage_checkpoint(old)
        runtime.commit_checkpoint({
            **old,
            "phase": "committed",
            "certificate": [1, 2, 3],
        })
        envelope = {**old, "peers": [{"userid": 3, "host": "127.0.0.1", "port": 12345}]}
        newer = {**self._envelope(2), "phase": "committed", "certificate": [1, 2, 3]}
        with (
            patch.object(
                runtime, "_query_peer", return_value={"epoch": 0, "sequence": 2}
            ),
            patch.object(runtime, "exchange", return_value={"envelope": newer}),
        ):
            actual = runtime._freshest_checkpoint(envelope, {})
        self.assertEqual(actual["sequence"], 2)

    def _cluster(self) -> dict[int, HostRuntime]:
        runtimes = {user: self._runtime() for user in (2, 3, 4)}
        proposal = self._envelope()
        proposal["peers"] = [
            {"userid": user, "host": "127.0.0.1", "port": runtime.control_port}
            for user, runtime in runtimes.items()
        ]
        proposal["digest"] = digest({
            key: value
            for key, value in proposal.items()
            if key not in {"phase", "digest"}
        })
        for user, runtime in runtimes.items():
            runtime.set_identity(user)
            self.assertTrue(runtime.stage_checkpoint(proposal))
            self.assertTrue(
                runtime.commit_checkpoint({
                    **proposal,
                    "phase": "committed",
                    "certificate": [1, 2, 3],
                })
            )
        self.now = LEASE_SECONDS + 1
        return runtimes

    def _request(self) -> dict[str, Any]:
        return {
            "session_id": "durable-room",
            "epoch": 0,
            "user_id": 2,
            "token": self.checkpoint["players"][1]["token"],
        }

    def test_two_survivors_of_four_cannot_promote(self) -> None:
        """Perder dos participantes conserva el estado y espera una mayoría."""
        runtimes = self._cluster()
        runtimes[4].close()
        for user in (2, 3):
            with self.assertRaisesRegex(ValueError, "mayoría"):
                runtimes[user].recover(self._request())
            self.assertIsNone(runtimes[user].server)

    def test_concurrent_candidates_converge_on_one_committing_authority(self) -> None:
        """La votación TCP concurrente conserva una única autoridad confirmable."""
        runtimes = self._cluster()
        request = self._request()

        def campaign(user: int) -> dict[str, Any]:
            try:
                return runtimes[user].recover(request)
            except ValueError:
                return {}

        with (
            patch.object(HostRuntime, "_announce"),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            list(pool.map(campaign, (2, 3)))
            result = campaign(2)
            if not result:
                result = campaign(3)
        self.assertEqual(result["mensaje"], "host_ready")
        owner = int(result["owner_id"])
        server = runtimes[owner].server
        self.assertIsNotNone(server)
        if server is not None:
            server.serialized(lambda: None)
            self.assertFalse(server.host_waiting_quorum)
            envelope = runtimes[owner].latest_checkpoint()
            self.assertIsNotNone(envelope)
            if envelope is not None:
                self.assertEqual(envelope["owner_id"], owner)
                for runtime in runtimes.values():
                    self.assertEqual(runtime.latest_checkpoint(), envelope)
        for user, runtime in runtimes.items():
            if user != owner and runtime.server is not None:
                replication = runtime.server.host_replication
                if replication is not None:
                    self.assertFalse(runtime.server.serialized(replication.publish))
