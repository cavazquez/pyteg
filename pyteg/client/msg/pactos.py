# ruff: noqa: PLR0913, D107, DOC201

"""Mensajes de pactos públicos de La Revancha."""

from __future__ import annotations

import json

from pyteg.client.msg.base import IMsg


class MsgProponerPacto(IMsg):
    """Propone un pacto visible para todos los jugadores."""

    def __init__(
        self,
        tipo: str,
        jugador_objetivo: int,
        *,
        paises: list[str] | None = None,
        continentes: list[str] | None = None,
        pais_objetivo: str | None = None,
        duracion: int | None = 1,
    ) -> None:
        self._data: dict[str, object] = {
            "mensaje": "proponer_pacto",
            "tipo": tipo,
            "jugador_objetivo": int(jugador_objetivo),
            "paises": list(paises or []),
            "continentes": list(continentes or []),
        }
        if pais_objetivo is not None:
            self._data["pais_objetivo"] = pais_objetivo
        if duracion is not None:
            self._data["duracion"] = int(duracion)

    def to_json(self) -> str:
        """Convierte la propuesta a JSON."""
        return json.dumps(self._data)


class MsgAceptarPacto(IMsg):
    """Acepta una propuesta pública."""

    def __init__(self, pacto_id: str) -> None:
        self._pacto_id = pacto_id

    def to_json(self) -> str:
        """Convierte la aceptación a JSON."""
        return json.dumps({"mensaje": "aceptar_pacto", "pacto_id": self._pacto_id})


class MsgRomperPacto(IMsg):
    """Anuncia la ruptura de un pacto."""

    def __init__(self, pacto_id: str) -> None:
        self._pacto_id = pacto_id

    def to_json(self) -> str:
        """Convierte la ruptura a JSON."""
        return json.dumps({"mensaje": "romper_pacto", "pacto_id": self._pacto_id})


__all__ = ["MsgAceptarPacto", "MsgProponerPacto", "MsgRomperPacto"]
