"""Sesión de tiempo real: cada participante valida y vota las transiciones.

Paxos por posición conserva el último valor aceptado incluso si cae el
proponente. La membresía cambia con mayorías del grupo anterior y del nuevo.
El almacenamiento se completa antes de responder a promesas, votos y commits.
"""

# ruff: noqa: DOC201, DOC501, TRY003, EM101, PLR2004, TRY301

from __future__ import annotations

import secrets
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from pyteg.network.peer_consensus import ConsensusSlot, ballot, previously_accepted
from pyteg.network.peer_state import (
    agreement,
    member_ids,
    sign,
    transition,
    valid_signature,
    validate_member,
    validate_state,
)
from pyteg.network.peer_transport import PeerPort, exchange
from pyteg.persistence.archive import MemoryRepository, digest, make_archive
from pyteg.persistence.peer_game import PeerGame
from pyteg.protocol import PROTOCOL_VERSION
from pyteg.server.hosting.consensus import majority
from pyteg.server.juego.estado import Estado

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.network.peer_consensus import Ballot
    from pyteg.persistence.archive import ArchiveRepository


def _votes_enough(
    members: list[dict[str, Any]],
    replies: list[dict[str, Any]],
    *,
    field: str = "voter",
    self_id: int | None = None,
) -> bool:
    votes = [reply[field] for reply in replies if field in reply]
    if self_id is not None:
        votes.append(self_id)
    return majority(member_ids(members), votes)


def _joint_votes(
    old: list[dict[str, Any]], new: list[dict[str, Any]], replies: list[dict[str, Any]]
) -> bool:
    return agreement(
        old, new, [reply["voter"] for reply in replies if "voter" in reply]
    )


class PeerNode:
    """Participante simétrico con motor, puerto y votos recuperables propios."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        advertise_host: str = "127.0.0.1",
        repository: ArchiveRepository | None = None,
    ) -> None:
        """Reserva recursos sin anunciar una sala parcialmente construida."""
        self._lock = threading.RLock()
        self._proposing = threading.Lock()
        self._stop = threading.Event()
        self._io = ThreadPoolExecutor(max_workers=16, thread_name_prefix="peer-io")
        self._repository = repository or MemoryRepository()
        self._port = PeerPort(self._handle, host=host, port=port)
        self._advertise_host = advertise_host
        self._slot = ConsensusSlot()
        self._document: dict[str, Any] = {}
        self._candidate: tuple[str, PeerGame] | None = None
        self._counter = time.time_ns()
        self._last_tick = time.monotonic()
        self._seen: dict[int, float] = {}
        self._receive: Callable[[int, dict[str, Any]], None] = lambda _uid, _msg: None
        self._changed: Callable[[], None] = lambda: None
        self._maintenance: threading.Thread | None = None
        self.user_id = 0
        self.token = ""
        self.key = ""
        self.game: PeerGame

    @property
    def port(self) -> int:
        """Obtiene el puerto de control de este participante."""
        return self._port.port

    @property
    def document(self) -> dict[str, Any]:
        """Entrega una copia del estado confirmado, sin exponer el voto mutable."""
        with self._lock:
            return deepcopy(self._document)

    @classmethod
    def create(cls, theme: str, name: str, profile: str, **options: Any) -> PeerNode:
        """Crea una sala: su creador tiene exactamente los mismos votos."""
        node = cls(**options)
        try:
            node.user_id, node.token, node.key = (
                1,
                secrets.token_hex(32),
                secrets.token_hex(32),
            )
            node.game = PeerGame.create(theme, name, node.token, profile)
            state: dict[str, Any] = {
                "version": 1,
                "session_id": uuid.uuid4().hex,
                "sequence": 0,
                "parent": None,
                "checkpoint": node.game.server.capture_state(),
                "members": [
                    {
                        "userid": 1,
                        "name": name,
                        "token": node.token,
                        "host": node._advertise_host,
                        "port": node.port,
                    }
                ],
                "clock": None,
                "next_userid": 2,
            }
            node._document = {
                "state": validate_state(state),
                "hash": digest(state),
                "certificate": None,
            }
            node._repository.start_room()
            node._repository.bind_session(state["session_id"], node.user_id)
            node._persist(node._document, node._slot)
            node._start()
        except Exception:
            node.close()
            raise
        return node

    @classmethod
    def join(
        cls,
        address: tuple[str, int],
        name: str,
        *,
        identity: tuple[int, str] | None = None,
        saved_archive: dict[str, Any] | None = None,
        **options: Any,
    ) -> PeerNode:
        """Se incorpora contactando a cualquier participante accesible."""
        node = cls(**options)
        try:
            info = exchange(
                address,
                {
                    "message": "peer_bootstrap",
                    "name": name,
                    "port": node.port,
                    "identity": list(identity) if identity else None,
                },
            )
            record = validate_member(info["member"])
            node.user_id, node.token, node.key = (
                record["userid"],
                record["token"],
                info["key"],
            )
            node._install_initial(info["document"])
            node._repository.bind_session(
                node._document["state"]["session_id"], node.user_id
            )
            # Una identidad reabierta reutiliza sus promesas, nunca las borra.
            saved = node._repository.load()
            if saved is None:
                saved = saved_archive
            if (
                saved is not None
                and "peer" in saved["payload"]
                and saved["payload"]["peer"]["document"]["state"]["session_id"]
                == info["document"]["state"]["session_id"]
            ):
                previous = saved["payload"]["peer"]
                if previous["token"] != node.token:
                    raise ValueError("El autoguardado pertenece a otra identidad")
                node._restore_saved(previous)
                node._install_document(info["document"])
            node._persist(node._document, node._slot)
            node._port.start()
            reply = exchange(address, node._packet("join", {"member": record}))
            node._install_document(reply["document"])
            node.start_maintenance()
        except Exception:
            node.close()
            raise
        return node

    @classmethod
    def open(cls, archive: dict[str, Any], **options: Any) -> PeerNode:
        """Reabre una identidad y consulta a sus pares sin sustituir sus votos."""
        saved = archive["payload"]["peer"]
        options.setdefault("port", saved["port"])
        node = cls(**options)
        try:
            node.user_id, node.token, node.key = (
                saved["userid"],
                saved["token"],
                saved["key"],
            )
            node._restore_saved(saved)
            node._repository.bind_session(
                node._document["state"]["session_id"], node.user_id
            )
            durable = node._repository.load()
            if durable is not None and "peer" in durable["payload"]:
                latest = durable["payload"]["peer"]
                if latest["token"] != node.token:
                    raise ValueError("La identidad guardada es incompatible")
                if (
                    latest["document"]["state"]["sequence"]
                    >= node._document["state"]["sequence"]
                ):
                    node._restore_saved(latest)
            node._persist(node._document, node._slot)
            node._start()
        except Exception:
            node.close()
            raise
        return node

    def _restore_saved(self, saved: dict[str, Any]) -> None:
        if type(self.user_id) is not int or not 1 <= self.user_id <= 2**31:
            raise ValueError("Identidad guardada inválida")
        for secret in (self.token, self.key):
            if not isinstance(secret, str) or len(secret) != 64:
                raise ValueError("Credencial guardada inválida")
            int(secret, 16)
        if saved["userid"] != self.user_id or saved["key"] != self.key:
            raise ValueError("El guardado no pertenece a esta sala")
        self._install_initial(saved["document"])
        self._slot = ConsensusSlot.restore(saved["slot"])
        if (
            self._slot.accepted_value is not None
            and self._slot.accepted_value["after"]["parent"] != self._document["hash"]
        ):
            raise ValueError("El voto guardado no continúa el estado confirmado")

    def _install_initial(self, document: dict[str, Any]) -> None:
        self._validate_document(document)
        state = document["state"]
        record = next(
            (
                item
                for item in state["checkpoint"]["players"]
                if item["userid"] == self.user_id
            ),
            None,
        )
        if record is not None and record["token"] != self.token:
            raise ValueError("Credencial de participante inválida")
        game = PeerGame.from_checkpoint(
            state["checkpoint"], self.user_id, 0, datetime.now(UTC).isoformat()
        )
        if hasattr(self, "game"):
            self.game.close()
        self.game = game
        self._document = deepcopy(document)
        self._seen = {uid: time.monotonic() for uid in member_ids(state["members"])}

    def _start(self) -> None:
        self._port.start()
        self.start_maintenance()

    def start_maintenance(self) -> None:
        """Activa sincronización, detección de desconexiones y reloj acordado."""
        if self._maintenance is None:
            self._maintenance = threading.Thread(
                target=self._maintain, name="peer-maintenance", daemon=True
            )
            self._maintenance.start()

    def set_callbacks(
        self,
        receive: Callable[[int, dict[str, Any]], None],
        changed: Callable[[], None],
    ) -> None:
        """Conecta notificaciones confirmadas con la cola de eventos de Qt."""
        with self._lock:
            self._receive, self._changed = receive, changed

    def sync_local(self) -> None:
        """Entrega la proyección privada y el tiempo confirmado de esta copia."""
        with self._lock:
            if self.user_id in member_ids(self._document["state"]["members"]):
                self.game.sync_player(self.user_id)
                self.game.publish(self._receive)
                clock = self._document["state"]["clock"]
                if clock:
                    self._receive(
                        self.user_id,
                        {"mensaje": "tiempo", "tiempo": clock["remaining"]},
                    )

    def _archive(self, document: dict[str, Any], slot: ConsensusSlot) -> dict[str, Any]:
        return make_archive(
            "game",
            {
                "peer": {
                    "userid": self.user_id,
                    "token": self.token,
                    "key": self.key,
                    "port": self.port,
                    "document": document,
                    "slot": slot.snapshot(),
                }
            },
        )

    def draft(self) -> dict[str, Any]:
        """Guarda el acuerdo y el voto pendiente juntos, incluida la identidad."""
        with self._lock:
            return self._archive(self._document, self._slot)

    def _persist(self, document: dict[str, Any], slot: ConsensusSlot) -> None:
        self._repository.save(self._archive(document, slot))

    def _packet(self, message: str, body: dict[str, Any]) -> dict[str, Any]:
        content = {
            "message": message,
            "session": self._document["state"]["session_id"],
            "actor": self.user_id,
            "body": body,
        }
        return {**content, "mac": sign(self.key, content)}

    def _vote_payload(
        self, value: dict[str, Any], number: Ballot, voter: int
    ) -> dict[str, Any]:
        return {
            "before": value["after"]["parent"],
            "hash": digest(value["after"]),
            "sequence": value["after"]["sequence"],
            "ballot": list(number),
            "old": member_ids(self._document["state"]["members"]),
            "voter": voter,
        }

    def _validate_document(self, document: dict[str, Any]) -> None:
        state = validate_state(document["state"])
        if digest(state) != document["hash"]:
            raise ValueError("La copia entre pares está alterada")
        if state["sequence"] == 0:
            if document["certificate"] is not None:
                raise ValueError("La sala inicial contiene votos inválidos")
            return
        certificate = document["certificate"]
        number = ballot(certificate["ballot"])
        votes = certificate["votes"]
        ids = [vote["voter"] for vote in votes]
        old = certificate["old"]
        if (
            len(ids) != len(set(ids))
            or not majority(old, ids)
            or not majority(member_ids(state["members"]), ids)
        ):
            raise ValueError("La transición no tiene mayorías de participantes")
        for vote in votes:
            payload = {
                "before": state["parent"],
                "hash": document["hash"],
                "sequence": state["sequence"],
                "ballot": list(number),
                "old": old,
                "voter": vote["voter"],
            }
            if not valid_signature(self.key, payload, vote["mac"]):
                raise ValueError("Certificado de pares inválido")

    def _install_document(  # noqa: C901, PLR0912 -- reemplazo atómico de documento, voto y motor.
        self, document: dict[str, Any], value: dict[str, Any] | None = None
    ) -> None:
        with self._lock:
            if self._stop.is_set():
                raise ValueError("La sesión está cerrada")
            self._validate_document(document)
            before = self._document["state"]
            after = document["state"]
            if after["session_id"] != before["session_id"]:
                raise ValueError("La copia pertenece a otra sala")
            if after["sequence"] < before["sequence"]:
                return
            if after["sequence"] == before["sequence"]:
                if document["hash"] != self._document["hash"]:
                    raise ValueError("Se detectaron dos estados en la misma posición")
                return
            if after["sequence"] == before["sequence"] + 1 and (
                after["parent"] != self._document["hash"]
                or document["certificate"]["old"] != member_ids(before["members"])
            ):
                raise ValueError("La transición no continúa esta partida")
            candidate = None
            if value and self._candidate and self._candidate[0] == digest(value):
                candidate = self._candidate[1]
            metadata_only = after["checkpoint"] == before["checkpoint"]
            if (
                candidate is None
                and value is not None
                and after["sequence"] == before["sequence"] + 1
                and not metadata_only
            ):
                reproduced, candidate, _result = transition(
                    before,
                    value["operation"],
                    value["seed"],
                    value["timestamp"],
                    self.user_id,
                )
                if digest(reproduced) != document["hash"]:
                    if candidate:
                        candidate.close()
                    raise ValueError(
                        "El commit no corresponde a la transición reproducida"
                    )
            if candidate is None and not metadata_only:
                candidate = PeerGame.from_checkpoint(
                    after["checkpoint"], self.user_id, 0, datetime.now(UTC).isoformat()
                )
            slot = ConsensusSlot()
            try:
                self._persist(document, slot)
            except Exception:
                if candidate is not None and (
                    self._candidate is None or candidate is not self._candidate[1]
                ):
                    candidate.close()
                raise
            previous_candidate = self._candidate
            self._candidate = None
            if candidate is not None:
                self.game.close()
                self.game = candidate
            if previous_candidate and previous_candidate[1] is not candidate:
                previous_candidate[1].close()
            if before["clock"] != after["clock"]:
                self._last_tick = time.monotonic()
            self._document, self._slot = deepcopy(document), slot
            for uid in member_ids(after["members"]):
                self._seen.setdefault(uid, time.monotonic())
            self.game.publish(self._receive)
            # Una copia recuperada no conserva los eventos transitorios del emisor.
            if candidate is not None and value is None:
                self.sync_local()
            if after["clock"]:
                self._receive(
                    self.user_id,
                    {"mensaje": "tiempo", "tiempo": after["clock"]["remaining"]},
                )
            self._changed()

    def _bootstrap(self, request: dict[str, Any], host: str) -> dict[str, Any]:
        with self._lock:
            state = self._document["state"]
            identity = request.get("identity")
            if identity is None:
                if (
                    state["checkpoint"]["state"]
                    not in {Estado.INICIAL, Estado.ESPERAR_JUGADORES}
                    or len(state["members"]) >= 8
                ):
                    raise ValueError("Esta sala no acepta nuevos jugadores")
                uid, token = state["next_userid"], secrets.token_hex(32)
            else:
                if not isinstance(identity, list) or len(identity) != 2:
                    raise ValueError("Identidad de reconexión inválida")
                uid, token = identity
                previous = next(
                    (
                        item
                        for item in state["checkpoint"]["players"]
                        if item["userid"] == uid
                    ),
                    None,
                )
                if previous is None or not secrets.compare_digest(
                    previous["token"], str(token)
                ):
                    raise ValueError("La identidad no pertenece a esta partida")
            member = validate_member({
                "userid": uid,
                "token": token,
                "name": request["name"],
                "host": host,
                "port": request["port"],
            })
            return {
                "member": member,
                "key": self.key,
                "document": deepcopy(self._document),
            }

    def _handle(self, request: dict[str, Any], host: str) -> dict[str, Any]:  # noqa: C901, PLR0911, PLR0912 -- límite autenticado de peticiones TCP.
        if self._stop.is_set():
            raise ValueError("Participante cerrado")
        if request.get("message") == "peer_bootstrap":
            return self._bootstrap(request, host)
        content = {
            field: request[field] for field in ("message", "session", "actor", "body")
        }
        if content["session"] != self._document["state"][
            "session_id"
        ] or not valid_signature(self.key, content, request.get("mac")):
            raise ValueError("Mensaje de pares no autenticado")
        actor, message, body = content["actor"], content["message"], content["body"]
        if type(actor) is not int or not isinstance(body, dict):
            raise ValueError("Mensaje de pares inválido")
        if message == "join":
            record = validate_member({**body["member"], "host": host})
            if record["userid"] != actor:
                raise ValueError("La identidad solicitada no coincide")
            historical = any(
                item["userid"] == actor
                for item in self._document["state"]["checkpoint"]["players"]
            )
            self.propose({
                "kind": "rejoin" if historical else "join",
                "actor": self.user_id,
                "id": uuid.uuid4().hex,
                "member": record,
            })
            return {"document": self.document}
        with self._lock:
            if actor not in member_ids(self._document["state"]["members"]):
                raise ValueError("El emisor ya no participa en el acuerdo")
            self._seen[actor] = time.monotonic()
            if message == "status":
                return {
                    "peer": self.user_id,
                    "document": deepcopy(self._document),
                    "pending": self._slot.accepted_value is not None,
                }
            if message == "commit":
                self._install_document(body["document"], body.get("value"))
                return {"ok": True, "peer": self.user_id}
            if body["before"] != self._document["hash"]:
                return {"document": deepcopy(self._document)}
            number = ballot(body["ballot"])
            if message == "prepare":
                slot = ConsensusSlot.restore(self._slot.snapshot())
                promise = slot.prepare(number)
                if promise is None:
                    return {"promised": list(self._slot.promised)}
                self._persist(self._document, slot)
                self._slot = slot
                proof = {"before": body["before"], "voter": self.user_id, **promise}
                return {**proof, "mac": sign(self.key, proof)}
            if message == "accept":
                return self._accept(body, number)
            raise ValueError("Petición de pares desconocida")

    def _accept(self, body: dict[str, Any], number: Ballot) -> dict[str, Any]:  # noqa: C901, PLR0912 -- validación y persistencia antes de emitir el voto.
        if number < self._slot.promised:
            return {"promised": list(self._slot.promised)}
        value, proofs = body["value"], body["proofs"]
        self._check_proofs(proofs, number, body["before"])
        accepted = previously_accepted(proofs)
        if accepted is not None:
            if digest(value) != digest(accepted):
                raise ValueError("La propuesta ignora un valor aceptado previamente")
        elif value["seed"] != digest(
            sorted((proof["voter"], proof["nonce"]) for proof in proofs)
        ):
            raise ValueError("La semilla no corresponde a los votos de preparación")
        operation = value["operation"]
        if (
            accepted is None
            and operation["kind"] == "tick"
            and time.monotonic() - self._last_tick < 0.95
        ):
            raise ValueError("El intervalo del reloj todavía no venció")
        if (
            accepted is None
            and operation["kind"] == "leave"
            and operation["target"] != operation["actor"]
            and time.monotonic() - self._seen.get(operation["target"], time.monotonic())
            < 8
        ):
            raise ValueError("El participante todavía responde")
        content = {key: item for key, item in operation.items() if key != "mac"}
        if not valid_signature(self.key, content, operation.get("mac")):
            raise ValueError("Acción de participante no autenticada")
        candidate = None
        if self._candidate is None or self._candidate[0] != digest(value):
            after, candidate, result = transition(
                self._document["state"],
                operation,
                value["seed"],
                value["timestamp"],
                self.user_id,
            )
            if digest(after) != digest(value["after"]) or result != value["result"]:
                if candidate:
                    candidate.close()
                raise ValueError("Las reglas no producen el estado propuesto")
        slot = ConsensusSlot.restore(self._slot.snapshot())
        if not slot.accept(number, value):
            if candidate:
                candidate.close()
            return {"promised": list(self._slot.promised)}
        try:
            self._persist(self._document, slot)
        except Exception:
            if candidate:
                candidate.close()
            raise
        self._slot = slot
        if candidate:
            if self._candidate:
                self._candidate[1].close()
            self._candidate = digest(value), candidate
        payload = self._vote_payload(value, number, self.user_id)
        return {"voter": self.user_id, "mac": sign(self.key, payload)}

    def _check_proofs(
        self, proofs: list[dict[str, Any]], number: Ballot, before: str
    ) -> None:
        ids = [proof["voter"] for proof in proofs]
        if len(ids) != len(set(ids)) or not majority(
            member_ids(self._document["state"]["members"]), ids
        ):
            raise ValueError("No hay una mayoría de promesas")
        for proof in proofs:
            content = {key: value for key, value in proof.items() if key != "mac"}
            if (
                proof["before"] != before
                or ballot(proof["ballot"]) != number
                or not valid_signature(self.key, content, proof["mac"])
            ):
                raise ValueError("Promesa de pares inválida")

    def _request(
        self, record: dict[str, Any], message: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        response = (
            self._handle(self._packet(message, body), "127.0.0.1")
            if record["userid"] == self.user_id
            else exchange((record["host"], record["port"]), self._packet(message, body))
        )
        with self._lock:
            self._seen[record["userid"]] = time.monotonic()
        return response

    def _collect(
        self,
        records: list[dict[str, Any]],
        message: str,
        body: dict[str, Any],
        enough: Callable[[list[dict[str, Any]]], bool],
    ) -> list[dict[str, Any]]:
        replies: list[dict[str, Any]] = []
        futures = [
            self._io.submit(self._request, record, message, body) for record in records
        ]
        for future in as_completed(futures):
            try:
                reply = future.result()
            except OSError, ValueError, KeyError, TypeError, RuntimeError:
                continue
            if "document" in reply:
                self._install_document(reply["document"])
            replies.append(reply)
            if enough(replies):
                break
        return replies

    def submit(self, command: dict[str, Any]) -> dict[str, Any] | None:
        """Propone un comando del propio jugador y devuelve su resultado confirmado."""
        command = deepcopy(command)
        command.setdefault("command_id", uuid.uuid4().hex)
        return self.propose({
            "kind": "command",
            "actor": self.user_id,
            "id": command["command_id"],
            "command": command,
        })

    def propose(self, operation: dict[str, Any]) -> dict[str, Any] | None:  # noqa: C901, PLR0914 -- fases y reintentos con membresía anterior y nueva.
        """Cualquier par puede finalizar un voto anterior antes de su acción."""
        operation = deepcopy(operation)
        operation.setdefault("id", uuid.uuid4().hex)
        operation["mac"] = sign(self.key, operation)
        with self._proposing:
            for _attempt in range(8):
                if self._stop.is_set():
                    raise ValueError("La sesión está cerrada")
                with self._lock:
                    before = deepcopy(self._document["state"])
                    previous_hash = self._document["hash"]
                    self._counter = max(self._counter + 1, self._slot.promised[0] + 1)
                    number = self._counter, self.user_id
                members = before["members"]
                body = {"before": previous_hash, "ballot": list(number)}
                prepared = self._collect(
                    members,
                    "prepare",
                    body,
                    partial(_votes_enough, members),
                )
                proofs = [item for item in prepared if "voter" in item]
                if self.document["hash"] != previous_hash:
                    continue
                if not majority(
                    member_ids(members), [item["voter"] for item in proofs]
                ):
                    if self._retry_ballot(prepared):
                        continue
                    raise ValueError(
                        "Falta una mayoría de participantes conectados; "
                        "la partida está pausada"
                    )
                value = previously_accepted(proofs)
                if value is None:
                    seed = digest(
                        sorted((proof["voter"], proof["nonce"]) for proof in proofs)
                    )
                    timestamp = datetime.now(UTC).isoformat()
                    after, candidate, result = transition(
                        before, operation, seed, timestamp, self.user_id
                    )
                    value = {
                        "operation": operation,
                        "seed": seed,
                        "timestamp": timestamp,
                        "after": after,
                        "result": result,
                    }
                    if candidate:
                        candidate.close()
                after_members = value["after"]["members"]
                records = {item["userid"]: item for item in members + after_members}
                accepted = self._collect(
                    list(records.values()),
                    "accept",
                    {**body, "proofs": proofs, "value": value},
                    partial(_joint_votes, members, after_members),
                )
                votes = [item for item in accepted if "voter" in item]
                if self.document["hash"] != previous_hash:
                    continue
                if not agreement(
                    members, after_members, [item["voter"] for item in votes]
                ):
                    if self._retry_ballot(accepted):
                        continue
                    raise ValueError(
                        "La transición quedó pendiente de confirmación; "
                        "se reintentará al recuperar una mayoría"
                    )
                document = {
                    "state": value["after"],
                    "hash": digest(value["after"]),
                    "certificate": {
                        "ballot": list(number),
                        "old": member_ids(members),
                        "votes": votes,
                    },
                }
                self._install_document(document, value)
                # Esperar la difusión evita que una acción inmediata use copias viejas.
                self._collect(
                    [
                        item
                        for item in records.values()
                        if item["userid"] != self.user_id
                    ],
                    "commit",
                    {"document": document, "value": value},
                    partial(
                        _votes_enough, after_members, field="peer", self_id=self.user_id
                    ),
                )
                if value["operation"]["id"] == operation["id"]:
                    return cast("dict[str, Any] | None", value["result"])
            raise ValueError("Hay propuestas simultáneas; reintentá la acción")

    def _retry_ballot(self, replies: list[dict[str, Any]]) -> bool:
        higher = [
            ballot(reply["promised"])[0] for reply in replies if "promised" in reply
        ]
        if not higher:
            return False
        with self._lock:
            self._counter = max(self._counter, *higher)
        return True

    def available(self) -> bool:
        """Sólo se puede jugar en el grupo que conserva una mayoría."""
        with self._lock:
            members = member_ids(self._document["state"]["members"])
            alive = [
                uid
                for uid in members
                if uid == self.user_id or time.monotonic() - self._seen.get(uid, 0) < 5
            ]
            return self.user_id in members and majority(members, alive)

    def _maintain(self) -> None:
        while not self._stop.wait(1):
            try:
                document = self.document
                if self.user_id not in member_ids(document["state"]["members"]):
                    self._rejoin(document)
                    continue
                members = document["state"]["members"]
                replies = self._collect(
                    [item for item in members if item["userid"] != self.user_id],
                    "status",
                    {},
                    partial(_votes_enough, members, field="peer", self_id=self.user_id),
                )
                if len(members) > 1 and not any("peer" in reply for reply in replies):
                    self._rejoin(self.document)
                    continue
                self._changed()
                with self._lock:
                    state = deepcopy(self._document["state"])
                    alive = [
                        uid
                        for uid in member_ids(state["members"])
                        if uid == self.user_id
                        or time.monotonic() - self._seen.get(uid, 0) < 5
                    ]
                    pending = self._slot.accepted_value
                    due = time.monotonic() - self._last_tick >= 0.95
                if (
                    self.user_id not in alive
                    or not majority(member_ids(state["members"]), alive)
                    or self.user_id != min(alive)
                    or self._proposing.locked()
                ):
                    continue
                missing = [
                    uid
                    for uid in member_ids(state["members"])
                    if uid not in alive
                    and time.monotonic() - self._seen.get(uid, 0) >= 8
                ]
                if missing:
                    self.propose({
                        "kind": "leave",
                        "actor": self.user_id,
                        "target": missing[0],
                    })
                elif pending is not None:
                    self.propose({
                        key: item
                        for key, item in pending["operation"].items()
                        if key != "mac"
                    })
                elif state["clock"] and due:
                    self.propose({"kind": "tick", "actor": self.user_id})
            except OSError, ValueError, KeyError, TypeError, RuntimeError:
                # Un voto pendiente conserva su valor y sus promesas al reintentar.
                continue

    def _rejoin(self, document: dict[str, Any]) -> None:
        previous = next(
            (
                item
                for item in document["state"]["checkpoint"]["players"]
                if item["userid"] == self.user_id
            ),
            None,
        )
        # Un alta interrumpida no tiene aún una identidad confirmada. Su puerto
        # sigue escuchando para que el proponente pueda terminar el acuerdo.
        if previous is None:
            return
        for member in document["state"]["members"]:
            if member["userid"] == self.user_id:
                continue
            try:
                address = member["host"], member["port"]
                info = exchange(
                    address,
                    {
                        "message": "peer_bootstrap",
                        "name": previous["username"],
                        "port": self.port,
                        "identity": [self.user_id, self.token],
                    },
                )
                self._install_document(info["document"])
                reply = exchange(
                    address, self._packet("join", {"member": info["member"]})
                )
                self._install_document(reply["document"])
            except OSError, ValueError, KeyError, TypeError:
                continue
            return

    def describe(self) -> dict[str, Any]:
        """Anuncia únicamente la sala y el endpoint público de este par."""
        state = self.document["state"]
        return {
            "message": "pyteg_room",
            "protocol": PROTOCOL_VERSION,
            "mode": "peer",
            "session_id": state["session_id"],
            "epoch": state["sequence"],
            "name": " / ".join(item["name"] for item in state["members"])[:120],
            "theme": state["checkpoint"]["theme"],
            "map_hash": state["checkpoint"]["map_hash"],
            "port": self.port,
            "players": len(state["members"]),
            "state": state["checkpoint"]["state"],
        }

    def close(self) -> None:
        """Detiene este par; los demás conservan el acuerdo y su propia escucha."""
        self._stop.set()
        self._port.close()
        if self._maintenance and self._maintenance is not threading.current_thread():
            self._maintenance.join(timeout=4)
        self._io.shutdown(wait=False, cancel_futures=True)
        with self._lock:
            if self._candidate:
                self._candidate[1].close()
                self._candidate = None
            if hasattr(self, "game"):
                self.game.close()
