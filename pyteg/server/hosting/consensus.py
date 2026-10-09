"""Mayorías, votos persistentes y leases de una única autoridad de sala."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

LEASE_SECONDS = 4.0


def majority(members: Iterable[int], acknowledgements: Iterable[int]) -> bool:
    """Comprueba una mayoría estricta sin contar IDs repetidos.

    Returns:
        True si más de la mitad de los integrantes confirmó.

    """
    voters = set(members)
    return (
        bool(voters) and len(voters.intersection(acknowledgements)) > len(voters) // 2
    )


def joint_majority(envelope: dict[str, Any], acknowledgements: Iterable[int]) -> bool:
    """Una incorporación o baja necesita mayoría de ambos grupos.

    Returns:
        True si confirmaron mayorías de la membresía anterior y la nueva.

    """
    ids = set(acknowledgements)
    return majority(envelope["members"], ids) and majority(
        envelope["previous_members"], ids
    )


class ElectionState:
    """Cada participante promete un candidato por época y conserva su lease."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Comienza sin autoridad ni voto."""
        self.term = 0
        self.voted_for: int | None = None
        self._deadline = 0.0
        self._clock = clock
        self._lock = threading.RLock()

    def export(self) -> dict[str, Any]:
        """Captura los votos para guardarlos antes de responder.

        Returns:
            Promesa de época y candidato, sin relojes dependientes del equipo.

        """
        with self._lock:
            return {
                "term": self.term,
                "voted_for": self.voted_for,
                "leased": self._deadline > self._clock(),
            }

    def restore(self, data: dict[str, Any]) -> None:
        """Restaura promesas y espera un lease completo después de reiniciar.

        Raises:
            ValueError: Si la promesa guardada no tiene una época válida.

        """
        if (
            type(data.get("term")) is not int
            or data["term"] < 0
            or (
                data.get("voted_for") is not None
                and (type(data["voted_for"]) is not int or data["voted_for"] <= 0)
            )
        ):
            msg = "Promesa de elección inválida"
            raise ValueError(msg)
        with self._lock:
            self.term = data["term"]
            self.voted_for = data["voted_for"]
            self._deadline = (
                self._clock() + LEASE_SECONDS if data.get("leased") else 0.0
            )

    def vote(self, term: int, candidate: int) -> bool:
        """Promete un candidato sólo cuando el lease anterior ya venció.

        Returns:
            True si este participante concedió o ya había concedido ese voto.

        """
        with self._lock:
            if term < self.term or (
                self._clock() < self._deadline and candidate != self.voted_for
            ):
                return False
            if term == self.term and self.voted_for not in {None, candidate}:
                return False
            if term > self.term:
                self.term = term
                self.voted_for = None
            self.voted_for = candidate
            return True

    def authorize(self, term: int, owner: int) -> bool:
        """Autoriza una preparación sin revocar votos ni acortar el lease.

        Returns:
            True si coincide con la promesa vigente.

        """
        with self._lock:
            return (
                term >= self.term
                and (term != self.term or self.voted_for in {None, owner})
                and (self._clock() >= self._deadline or self.voted_for in {None, owner})
            )

    def renew(self, term: int, owner: int) -> None:
        """Conserva un lease al confirmar una copia de la autoridad vigente."""
        with self._lock:
            self.term = max(self.term, term)
            self.voted_for = owner
            self._deadline = self._clock() + LEASE_SECONDS
