"""Resumen público de una entrega, sin restaurar ni modificar el motor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyteg.persistence.archive import validate_archive
from pyteg.persistence.asynchronous import AsyncGame
from pyteg.persistence.history import Replay


@dataclass(frozen=True)
class TurnPreview:
    """Identidades, ronda y cambios visibles del turno recibido."""

    author: str
    recipient: str
    step: int
    snapshot: dict[str, Any]
    changes: dict[str, dict[str, Any]]
    time: str

    @classmethod
    def from_archive(
        cls, archive: dict[str, Any], before: dict[str, Any] | None = None
    ) -> TurnPreview:
        """Verifica integridad e historial antes de construir el resumen.

        Returns:
            Vista que contiene únicamente datos públicos del historial.

        Raises:
            ValueError: Si la entrega no tiene un estado público válido.

        """
        payload = validate_archive(archive, kind="turn")["payload"]
        AsyncGame._validate_turn(payload)  # noqa: SLF001 -- mismo contrato de entrega.
        history = payload["checkpoint"].get("history")
        replay = Replay(history)
        if not replay.count:
            msg = "El turno no contiene un historial público"
            raise ValueError(msg)
        snapshot = replay.snapshot(replay.count - 1)
        names = {
            player["userid"]: str(player["username"]) for player in snapshot["players"]
        }
        if payload["author"] not in names or payload["holder"] not in names:
            msg = "La entrega contiene identidades desconocidas"
            raise ValueError(msg)
        previous = before.get("countries", {}) if before else {}
        changes = {
            name: data
            for name, data in snapshot["countries"].items()
            if before is not None and previous.get(name) != data
        }
        records = history["records"]
        return cls(
            names[payload["author"]],
            names[payload["holder"]],
            payload["step"],
            snapshot,
            changes,
            records[-1]["time"] if records else "",
        )
