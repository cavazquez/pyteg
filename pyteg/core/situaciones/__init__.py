"""Reglas de cartas de situación independientes del mapa."""

from pyteg.core.situaciones.catalog import (
    DEFAULT_SITUATION_RULESET,
    available_situation_rulesets,
    build_situation_deck,
)
from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.model import (
    NoSituationCard,
    SituationCard,
    SituationContext,
    SituationState,
)
from pyteg.core.situaciones.runtime import SituationRuntime

__all__ = [
    "DEFAULT_SITUATION_RULESET",
    "NoSituationCard",
    "SituationCard",
    "SituationContext",
    "SituationDeck",
    "SituationRuntime",
    "SituationState",
    "available_situation_rulesets",
    "build_situation_deck",
]
