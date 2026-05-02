"""TypedDict para payloads de mensajes salientes del servidor.

Estos `TypedDict` capturan la forma del `dict` que cada `IMsg` recibe en su
constructor (y que termina viajando como JSON al cliente). Los campos
opcionales se modelan en una clase secundaria con `total=False`.
"""

from __future__ import annotations

from typing import TypedDict


class _BattleResultRequired(TypedDict):
    """Campos obligatorios del payload de `MsgResultadoBatalla`."""

    origen: str
    destino: str
    dados_atacante: list[int]
    dados_defensor: list[int]
    resultado: dict[str, list[str]]


class BattleResultPayload(_BattleResultRequired, total=False):
    """Payload de `MsgResultadoBatalla` (incluye campos opcionales)."""

    atacante_id: int | None
    defensor_id: int | None
    atacante: str
    defensor: str
    conquistado: bool


class _MissileResultRequired(TypedDict):
    """Campos obligatorios del payload de `MsgResultadoMisil`."""

    pais_origen: str
    pais_destino: str
    distancia: int
    dano: int
    unidades_restantes: int


class MissileResultPayload(_MissileResultRequired, total=False):
    """Payload de `MsgResultadoMisil` (incluye campos opcionales)."""

    jugador_id: int | None
    jugador: str


class JugadorListaItem(TypedDict):
    """Item de la lista enviada en `MsgActualizarListaJugadores`."""

    userid: int
    color: dict[str, int]
