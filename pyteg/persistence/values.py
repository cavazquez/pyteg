"""Codec JSON de valores del dominio, sin deserialización ejecutable."""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
from pyteg.core.partida.pactos import Pact
from pyteg.core.situaciones.model import SituationCard, SituationState

_CARD_FIELDS = ("_pais", "_simbolo", "_tipo", "_continente", "_usado", "_jugador")
_MAX_DEPTH = 32


def pack(value: Any) -> Any:
    """Convierte sólo contenedores y valores conocidos del juego a JSON.

    Returns:
        Valor JSON que conserva los tipos admitidos del dominio.

    Raises:
        ValueError: Si los datos no son compatibles o la sesión no es válida.

    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [pack(item) for item in value]
    if isinstance(value, dict):
        return {"kind": "dict", "items": [[pack(k), pack(v)] for k, v in value.items()]}
    if isinstance(value, (tuple, set, frozenset)):
        return {"kind": type(value).__name__, "items": [pack(v) for v in value]}
    if isinstance(value, TarjetaDePais):
        return {
            "kind": "country_card",
            "items": [pack(getattr(value, k)) for k in _CARD_FIELDS],
        }
    for cls, kind in (
        (SituationCard, "situation_card"),
        (SituationState, "situation_state"),
        (Pact, "pact"),
    ):
        if isinstance(value, cls):
            return {
                "kind": kind,
                "items": {
                    field.name: pack(getattr(value, field.name))
                    for field in fields(cls)
                },
            }
    msg = f"Valor no permitido en una copia de recuperación: {type(value).__name__}"
    raise ValueError(msg)


def unpack(value: Any, depth: int = 0) -> Any:
    """Reconstruye datos con una lista cerrada de tipos y profundidad limitada.

    Returns:
        Valor del dominio reconstruido a partir de datos JSON.

    Raises:
        ValueError: Si los datos no son compatibles o la sesión no es válida.

    """
    if depth > _MAX_DEPTH:
        msg = "Copia de recuperación demasiado anidada"
        raise ValueError(msg)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [unpack(item, depth + 1) for item in value]
    if not isinstance(value, dict) or set(value) != {"kind", "items"}:
        msg = "Valor de recuperación inválido"
        raise ValueError(msg)
    kind, items = value["kind"], value["items"]
    if kind == "dict" and isinstance(items, list):
        return {unpack(k, depth + 1): unpack(v, depth + 1) for k, v in items}
    containers = {"tuple": tuple, "set": set, "frozenset": frozenset}
    if kind in containers and isinstance(items, list):
        return containers[kind](unpack(v, depth + 1) for v in items)
    if (
        kind == "country_card"
        and isinstance(items, list)
        and len(items) == len(_CARD_FIELDS)
    ):
        decoded = [unpack(v, depth + 1) for v in items]
        card = TarjetaDePais(
            decoded[0], decoded[1], tipo=decoded[2], continente=decoded[3]
        )
        card._usado, card._jugador = decoded[4:]  # noqa: SLF001
        return card
    classes = {
        "situation_card": SituationCard,
        "situation_state": SituationState,
        "pact": Pact,
    }
    if kind in classes and isinstance(items, dict):
        cls = classes[kind]
        if set(items) == {field.name for field in fields(cls)}:
            return cls(**{k: unpack(v, depth + 1) for k, v in items.items()})
    msg = "Tipo de recuperación desconocido o campos inválidos"
    raise ValueError(msg)


def capture(obj: Any, names: tuple[str, ...]) -> dict[str, Any]:
    """Captura los atributos declarados de un componente.

    Returns:
        Atributos declarados del componente, convertidos a JSON.

    """
    return {name: pack(getattr(obj, name)) for name in names}


def restore(obj: Any, state: dict[str, Any], names: tuple[str, ...]) -> None:
    """Restaura exactamente los atributos permitidos por el componente.

    Raises:
        ValueError: Si los datos no son compatibles o la sesión no es válida.

    """
    if set(state) != set(names):
        msg = "Campos de recuperación incompatibles"
        raise ValueError(msg)
    for name in names:
        setattr(obj, name, unpack(state[name]))
