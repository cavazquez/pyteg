"""Modelo de estado del cliente sin dependencia de Qt.

La conexión Qt puede alimentar este modelo y la GUI consumir sus señales o
adaptadores. Los bots y las pruebas pueden usar exactamente el mismo código.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApplyEventResult:
    """Resultado de aplicar un evento versionado."""

    applied: bool
    duplicate: bool = False
    gap: bool = False


@dataclass
class ClientStateModel:
    """Estado público reconstruido desde snapshots y eventos del servidor."""

    # ``-1`` representa que todavía no se recibió ningún snapshot. La revisión
    # pública cero es válida para el lobby inicial y debe poder aplicarse.
    revision: int = -1
    snapshot: dict[str, Any] = field(default_factory=dict)
    command_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_phase: str | None = None
    protocol_version: str | None = None
    theme: str | None = None
    map_hash: str | None = None
    handshake_accepted: bool = False
    _gap_detected: bool = field(default=False, init=False, repr=False)

    def apply_event(self, event: dict[str, Any]) -> ApplyEventResult:
        """Aplica un evento; ignora duplicados y señala huecos de revisión.

        Returns:
            Resultado que indica si se aplicó, fue duplicado o dejó un hueco.

        """
        kind = event.get("mensaje")
        if kind == "hello":
            self.protocol_version = str(event["protocol_version"])
            self.theme = str(event["theme"])
            self.map_hash = str(event["map_hash"])
            return ApplyEventResult(applied=True)
        if kind == "hello_ack":
            self.handshake_accepted = bool(event["accepted"])
            return ApplyEventResult(applied=True)
        if kind == "snapshot":
            revision = int(event["revision"])
            if revision <= self.revision:
                return ApplyEventResult(applied=False, duplicate=True)
            gap = self.revision >= 0 and revision != self.revision + 1
            self.snapshot = {
                key: value for key, value in event.items() if key != "mensaje"
            }
            self.revision = revision
            self.last_phase = event.get("fase")
            self._gap_detected = gap
            return ApplyEventResult(applied=True, gap=gap)
        if kind == "command_result":
            command_id = str(event["command_id"])
            self.command_results[command_id] = dict(event)
            return ApplyEventResult(applied=True)
        if kind == "fase":
            self.last_phase = str(event["fase"])
        return ApplyEventResult(applied=True)

    def needs_snapshot(self) -> bool:
        """Indica si una aplicación anterior detectó un hueco.

        Returns:
            ``True`` cuando el modelo marcó un hueco pendiente de resincronizar.

        """
        return self._gap_detected
