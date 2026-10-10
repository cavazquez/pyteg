"""Cadena de membresía firmada para verificar identidades al recuperar pares."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101, PLR2004

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pyteg.network.identity import Identity, public_key, validate_identities, verify
from pyteg.network.peer_state import agreement, member_ids, validate_member
from pyteg.persistence.archive import digest

_MAX_MEMBERSHIP_CHANGES = 4096


def initial_trust(state: dict[str, Any], identity: Identity) -> list[dict[str, Any]]:
    """Firma el origen de la sala con la identidad fijada por su invitación."""
    body = {
        "session": state["session_id"],
        "sequence": 0,
        "parent": None,
        "old": [],
        "members": deepcopy(state["members"]),
        "identities": deepcopy(state["identities"]),
        "origin": digest(state),
    }
    return [{"body": body, "votes": [{"voter": 1, "signature": identity.sign(body)}]}]


def membership_body(
    before: dict[str, Any], after: dict[str, Any], trust: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Vincula cada cambio de participantes con las identidades ya autorizadas."""
    if before["members"] == after["members"]:
        if before["identities"] != after["identities"]:
            raise ValueError("Las identidades no pueden cambiar sin una incorporación")
        return None
    return {
        "session": before["session_id"],
        "sequence": after["sequence"],
        "parent": digest(trust[-1]),
        "old": member_ids(before["members"]),
        "members": deepcopy(after["members"]),
        "identities": deepcopy(after["identities"]),
        "origin": trust[0]["body"]["origin"],
    }


def validate_trust(  # noqa: C901, PLR0912 -- cadena de incorporaciones y bajas.
    trust: object,
    state: dict[str, Any],
    root_key: str,
    previous: list[dict[str, Any]] | None = None,
) -> None:
    """Verifica todas las incorporaciones sin confiar en claves de un estado nuevo."""
    if not isinstance(trust, list) or not 1 <= len(trust) <= _MAX_MEMBERSHIP_CHANGES:
        raise ValueError("Falta la cadena de identidades de la sala")
    public_key(root_key)
    if (
        previous is not None
        and trust[: min(len(trust), len(previous))] != previous[: len(trust)]
    ):
        raise ValueError("La cadena de identidades no continúa esta sala")
    keys: dict[str, str] = {}
    members: list[dict[str, Any]] = []
    last_sequence = -1
    for index, entry in enumerate(trust):
        if not isinstance(entry, dict) or set(entry) != {"body", "votes"}:
            raise ValueError("Certificado de identidad inválido")
        body = entry["body"]
        if not isinstance(body, dict) or set(body) != {
            "session",
            "sequence",
            "parent",
            "old",
            "members",
            "identities",
            "origin",
        }:
            raise ValueError("Campos del certificado de identidad inválidos")
        new_keys = validate_identities(body["identities"])
        if not isinstance(body["members"], list) or not 1 <= len(body["members"]) <= 8:
            raise ValueError("Participantes del certificado inválidos")
        new_members = [validate_member(item) for item in body["members"]]
        ids = member_ids(new_members)
        if ids != sorted(set(ids)) or any(
            new_keys.get(str(item["userid"])) != item["public_key"]
            for item in new_members
        ):
            raise ValueError("Claves de participantes incompatibles")
        if (
            body["session"] != state["session_id"]
            or type(body["sequence"]) is not int
            or not last_sequence < body["sequence"] <= state["sequence"]
        ):
            raise ValueError("Posición del certificado de identidad inválida")
        if any(new_keys.get(uid) != key for uid, key in keys.items()):
            raise ValueError("Se intentó reemplazar la identidad de un jugador")
        if index == 0:
            if (
                body["sequence"] != 0
                or body["parent"] is not None
                or body["old"] != []
                or ids != [1]
                or new_keys != {"1": root_key}
            ):
                raise ValueError("Origen de sala incompatible con la invitación")
            voters = [1]
        else:
            if (
                body["parent"] != digest(trust[index - 1])
                or body["old"] != member_ids(members)
                or body["origin"] != trust[0]["body"]["origin"]
            ):
                raise ValueError("El certificado no continúa la membresía anterior")
            voters = body["old"]
        votes = entry["votes"]
        if not isinstance(votes, list) or len(votes) > 8:
            raise ValueError("Votos de identidad inválidos")
        received = [vote["voter"] for vote in votes]
        if len(received) != len(set(received)) or not agreement(
            members if index else new_members, new_members, received
        ):
            raise ValueError("La incorporación no tiene mayorías firmadas")
        for vote in votes:
            uid = vote["voter"]
            key = (
                keys.get(str(uid))
                if uid in voters and index
                else new_keys.get(str(uid))
            )
            if key is None or not verify(key, body, vote.get("signature")):
                raise ValueError("Firma de incorporación inválida")
        keys, members, last_sequence = new_keys, new_members, body["sequence"]
    if state["members"] != members or state["identities"] != keys:
        raise ValueError("El estado no coincide con las identidades autorizadas")
    if state["sequence"] == 0 and digest(state) != trust[0]["body"]["origin"]:
        raise ValueError("El origen de la sala fue alterado")
