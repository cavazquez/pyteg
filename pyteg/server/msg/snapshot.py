"""Mensajes públicos de revisión e idempotencia."""

from __future__ import annotations

import json
from typing import Any

from pyteg.server.msg.base import IMsg


class MsgSnapshot(IMsg):
    """Snapshot público atómico; nunca incluye tarjetas ni objetivos secretos."""

    def __init__(self, snapshot: dict[str, Any]) -> None:
        """Inicializa el snapshot público."""
        self._snapshot = {"mensaje": "snapshot", **snapshot}

    def to_json(self) -> str:
        """Serializa el snapshot.

        Returns:
            JSON del snapshot.

        """
        return json.dumps(self._snapshot, ensure_ascii=False)


class MsgCommandResult(IMsg):
    """Resultado estable de un comando, apto para reintentos idempotentes."""

    def __init__(
        self,
        command_id: str,
        accepted: bool,  # noqa: FBT001
        revision: int,
        error_code: str | None = None,
    ) -> None:
        """Inicializa el resultado estable."""
        self._data: dict[str, Any] = {
            "mensaje": "command_result",
            "command_id": command_id,
            "accepted": accepted,
            "revision": revision,
        }
        if error_code:
            self._data["error_code"] = error_code

    def to_json(self) -> str:
        """Serializa el resultado.

        Returns:
            JSON del resultado.

        """
        return json.dumps(self._data)
