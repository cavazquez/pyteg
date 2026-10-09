"""Votos durables por transición, sin un coordinador permanente."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

import secrets
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

from pyteg.persistence.archive import digest

type Ballot = tuple[int, int]


def ballot(value: object) -> Ballot:
    """Valida un número de propuesta total y único por participante."""
    if (
        not isinstance(value, list)
        or len(value) != 2  # noqa: PLR2004 -- contador e identidad.
        or any(type(item) is not int or item < 0 for item in value)
        or value[0] > 2**63
        or not 1 <= value[1] <= 2**31
    ):
        raise ValueError("Número de propuesta inválido")
    return value[0], value[1]


@dataclass
class ConsensusSlot:
    """Acceptor de Paxos: promete antes de responder y retiene lo aceptado."""

    promised: Ballot = (0, 0)
    accepted_ballot: Ballot = (0, 0)
    accepted_value: dict[str, Any] | None = None
    nonce: str = field(default_factory=lambda: secrets.token_hex(32))

    def prepare(self, number: Ballot) -> dict[str, Any] | None:
        """Promete una propuesta sin olvidar valores aceptados anteriormente."""
        if number < self.promised:
            return None
        if number > self.promised:
            self.promised = number
            self.nonce = secrets.token_hex(32)
        return {
            "ballot": list(number),
            "nonce": self.nonce,
            "accepted": (
                {
                    "ballot": list(self.accepted_ballot),
                    "value": deepcopy(self.accepted_value),
                }
                if self.accepted_value is not None
                else None
            ),
        }

    def accept(self, number: Ballot, value: dict[str, Any]) -> bool:
        """Acepta una transición validada sin cambiar el valor del mismo voto."""
        if number < self.promised:
            return False
        if (
            self.accepted_ballot == number
            and self.accepted_value is not None
            and digest(self.accepted_value) != digest(value)
        ):
            return False
        self.promised = self.accepted_ballot = number
        self.accepted_value = deepcopy(value)
        return True

    def snapshot(self) -> dict[str, Any]:
        """Obtiene el voto que debe guardarse antes de confirmar al emisor."""
        return {
            "promised": list(self.promised),
            "accepted_ballot": list(self.accepted_ballot),
            "accepted_value": deepcopy(self.accepted_value),
            "nonce": self.nonce,
        }

    @classmethod
    def restore(cls, state: dict[str, Any]) -> ConsensusSlot:
        """Recupera promesas sin permitir un segundo voto después de reiniciar."""

        # (0, 0) es el único valor inicial sin identidad de proponente.
        def saved_number(value: object) -> Ballot:
            return (0, 0) if value == [0, 0] else ballot(value)

        promised = saved_number(state.get("promised"))
        accepted = saved_number(state.get("accepted_ballot"))
        value = state.get("accepted_value")
        nonce = state.get("nonce")
        if (
            accepted > promised
            or (value is not None and not isinstance(value, dict))
            or (value is None) != (accepted == (0, 0))
        ):
            raise ValueError("Voto guardado inválido")
        if not isinstance(nonce, str) or len(nonce) != 64:  # noqa: PLR2004 -- nonce de 256 bits.
            raise ValueError("Nonce de voto guardado inválido")
        int(nonce, 16)
        return cls(promised, accepted, deepcopy(value), nonce)


def previously_accepted(replies: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Conserva el valor del mayor voto previo al cambiar de proponente."""
    values = [reply["accepted"] for reply in replies if reply.get("accepted")]
    if not values:
        return None
    latest = max(values, key=lambda item: ballot(item["ballot"]))
    return cast("dict[str, Any]", deepcopy(latest["value"]))
