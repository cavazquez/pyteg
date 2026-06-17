"""Excepciones personalizadas del proyecto.

Reexporta todas las excepciones de PyTeg para preservar
"from pyteg.exceptions import X". Organización interna por familia:

- `base`: jerarquía raíz (`PyTegError`).
- `system`: errores del sistema (mensajes inválidos, estados, recursos).
- `game_rules`: violaciones de reglas del juego (`GameRuleViolationError`
  y subclases).
"""

from __future__ import annotations

from pyteg.exceptions.base import PyTegError
from pyteg.exceptions.game_rules import (
    CountryNotFoundError,
    CountryNotOwnedError,
    GameNotStartedError,
    GameRuleViolationError,
    InsufficientUnitsError,
    InvalidActionError,
    MissileOutOfRangeError,
    MissilesNotEnabledError,
    MissingFieldError,
    NoMissilesAvailableError,
    NotPlayerTurnError,
)
from pyteg.exceptions.system import (
    EstadoInvalidoError,
    ImagenNoEncontradaError,
    MensajeNoValidoError,
)

__all__ = [
    "CountryNotFoundError",
    "CountryNotOwnedError",
    "EstadoInvalidoError",
    "GameNotStartedError",
    "GameRuleViolationError",
    "ImagenNoEncontradaError",
    "InsufficientUnitsError",
    "InvalidActionError",
    "MensajeNoValidoError",
    "MissileOutOfRangeError",
    "MissilesNotEnabledError",
    "MissingFieldError",
    "NoMissilesAvailableError",
    "NotPlayerTurnError",
    "PyTegError",
]
