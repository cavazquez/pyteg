"""Estado y transiciones verificables del modo entre pares."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101, PLR2004, TRY301, PLR0916
# Los guardas reúnen todos los límites de cada esquema recibido por la red.

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import operator
from copy import deepcopy
from datetime import datetime
from typing import Any

from pyteg.persistence.archive import canonical_bytes, digest
from pyteg.persistence.peer_game import PeerGame
from pyteg.protocol import map_hash_for_theme
from pyteg.server.hosting.consensus import majority

PEER_STATE_VERSION = 1


def member_ids(members: list[dict[str, Any]]) -> list[int]:
    """Obtiene IDs distintos, sin contar nombres ni direcciones repetidas."""
    return [item["userid"] for item in members]


def agreement(
    old: list[dict[str, Any]], new: list[dict[str, Any]], votes: list[int]
) -> bool:
    """Una transición de participantes necesita mayorías de ambos grupos."""
    return majority(member_ids(old), votes) and majority(member_ids(new), votes)


def validate_member(record: object) -> dict[str, Any]:
    """Valida identidades y endpoints antes de abrir conexiones o motores."""
    if not isinstance(record, dict) or set(record) != {
        "userid",
        "name",
        "token",
        "host",
        "port",
    }:
        raise ValueError("Participante de pares inválido")
    if (
        type(record["userid"]) is not int
        or not 1 <= record["userid"] <= 2**31
        or type(record["port"]) is not int
        or not 1 <= record["port"] <= 65535
        or not isinstance(record["name"], str)
        or not 0 < len(record["name"].strip()) <= 80
        or not isinstance(record["token"], str)
        or len(record["token"]) != 64
        or not isinstance(record["host"], str)
    ):
        raise ValueError("Participante de pares inválido")
    ipaddress.IPv4Address(record["host"])
    int(record["token"], 16)
    return deepcopy(record)


def validate_state(state: object) -> dict[str, Any]:
    """Valida el documento compartido; el motor valida su propio checkpoint."""
    if not isinstance(state, dict):
        raise ValueError("Estado de pares inválido")  # noqa: TRY004 -- error uniforme para archivos y red.
    required = {
        "version",
        "session_id",
        "sequence",
        "parent",
        "checkpoint",
        "members",
        "clock",
        "next_userid",
    }
    if (
        set(state) != required
        or type(state["version"]) is not int
        or state["version"] != PEER_STATE_VERSION
    ):
        raise ValueError("Versión o campos del estado de pares incompatibles")
    if (
        not isinstance(state["session_id"], str)
        or len(state["session_id"]) != 32
        or type(state["sequence"]) is not int
        or not 0 <= state["sequence"] <= 2**31
        or type(state["next_userid"]) is not int
        or not 1 <= state["next_userid"] <= 2**31
        or not isinstance(state["checkpoint"], dict)
        or not isinstance(state["members"], list)
        or not 1 <= len(state["members"]) <= 8
    ):
        raise ValueError("Estado de pares inválido")
    members = [validate_member(item) for item in state["members"]]
    int(state["session_id"], 16)
    ids = member_ids(members)
    if ids != sorted(set(ids)) or state["next_userid"] <= max(ids):
        raise ValueError("Identidades de pares incompatibles")
    if state["sequence"] == 0:
        if state["parent"] is not None:
            raise ValueError("La sala inicial no puede tener una transición anterior")
    elif not isinstance(state["parent"], str) or len(state["parent"]) != 64:
        raise ValueError("Falta la transición anterior")
    else:
        int(state["parent"], 16)
    checkpoint = state["checkpoint"]
    if checkpoint.get("theme") not in {"classic", "revancha"} or checkpoint.get(
        "map_hash"
    ) != map_hash_for_theme(checkpoint["theme"]):
        raise ValueError("Mapa incompatible en la sala entre pares")
    clock = state["clock"]
    if clock is not None and (
        not isinstance(clock, dict)
        or set(clock) != {"marker", "remaining"}
        or not isinstance(clock["marker"], list)
        or len(clock["marker"]) != 3
        or any(type(item) is not int or item < 0 for item in clock["marker"])
        or type(clock["remaining"]) is not int
        or not 1 <= clock["remaining"] <= 86400
    ):
        raise ValueError("Reloj compartido inválido")
    return deepcopy(state)


def sign(key: str, value: object) -> str:
    """Autentica mensajes entre los participantes de confianza de la sala."""
    return hmac.new(
        key.encode("ascii"), canonical_bytes(value), hashlib.sha256
    ).hexdigest()


def valid_signature(key: str, value: object, signature: object) -> bool:
    """Comprueba un MAC sin tratar los certificados como protección antitrampas."""
    return isinstance(signature, str) and hmac.compare_digest(
        sign(key, value), signature
    )


def _clock_after(
    game: PeerGame, previous: dict[str, Any] | None
) -> dict[str, Any] | None:
    snapshot = game.server.public_snapshot()
    turn = snapshot.get("turno")
    if snapshot.get("estado") != "JUGANDO" or not isinstance(turn, dict):
        return None
    marker = [turn["num_ronda"], turn["num_turno"], turn["jugador_id"]]
    if previous is not None and previous["marker"] == marker:
        return deepcopy(previous)
    return {
        "marker": marker,
        "remaining": snapshot["configuracion"]["segundos_por_turno"],
    }


def transition(  # noqa: C901, PLR0912, PLR0915 -- una transición completa se valida antes de devolver su candidato.
    before: dict[str, Any],
    operation: dict[str, Any],
    seed: str,
    timestamp: str,
    local_id: int,
) -> tuple[dict[str, Any], PeerGame | None, dict[str, Any] | None]:
    """Ejecuta la transición en un candidato descartable y obtiene su estado."""
    validate_state(before)
    if not isinstance(seed, str) or len(seed) != 64:
        raise ValueError("Semilla de transición inválida")
    int(seed, 16)
    if not isinstance(timestamp, str) or len(timestamp) > 60:
        raise ValueError("Marca temporal de transición inválida")
    datetime.fromisoformat(timestamp)
    actor = operation.get("actor")
    if type(actor) is not int or actor not in member_ids(before["members"]):
        raise ValueError("La acción no corresponde a un participante conectado")
    kind = operation.get("kind")
    after = deepcopy(before)
    after["sequence"] += 1
    after["parent"] = digest(before)
    clock = before["clock"]
    if kind == "tick" and clock is not None and clock["remaining"] > 1:
        after["clock"]["remaining"] -= 1
        return after, None, None
    if kind == "tick" and clock is None:
        raise ValueError("No hay un reloj activo")
    game = PeerGame.from_checkpoint(
        before["checkpoint"], local_id, int(seed, 16), timestamp
    )
    try:
        result = None
        if kind in {"join", "rejoin"}:
            record = validate_member(operation.get("member"))
            existing = next(
                (
                    item
                    for item in before["members"]
                    if item["userid"] == record["userid"]
                ),
                None,
            )
            if kind == "join":
                if (
                    not (
                        game.server.estado.es_inicial()
                        or game.server.estado.es_esperando_jugadores()
                    )
                    or record["userid"] != before["next_userid"]
                ):
                    raise ValueError(
                        "Los nuevos jugadores sólo pueden ingresar al lobby"
                    )
                after["next_userid"] += 1
            elif existing is not None and existing["token"] != record["token"]:
                raise ValueError("Credencial de reconexión inválida")
            if existing is None:
                if len(before["members"]) >= 8:
                    raise ValueError("La sala ya tiene ocho participantes")
                game.apply_operation(operation)
            after["members"] = sorted(
                [
                    item
                    for item in before["members"]
                    if item["userid"] != record["userid"]
                ]
                + [record],
                key=operator.itemgetter("userid"),
            )
        elif kind == "leave":
            target = operation.get("target")
            if (
                target not in member_ids(before["members"])
                or len(before["members"]) <= 1
            ):
                raise ValueError("La baja no corresponde a un participante de la sala")
            game.apply_operation(operation)
            after["members"] = [
                item for item in before["members"] if item["userid"] != target
            ]
        elif kind == "tick":
            game.apply_operation({"kind": "expire"})
        elif kind == "command":
            result = game.apply_operation(operation)
        else:
            raise ValueError("Operación de pares desconocida")
        after["checkpoint"] = game.server.capture_state()
        after["clock"] = _clock_after(game, clock)
        validate_state(after)
    except Exception:
        game.close()
        raise
    return after, game, result
