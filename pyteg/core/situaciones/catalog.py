"""Catálogo y fábrica de efectos de situación."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.effects import (
    ClassicCombatEffect,
    ClosedBordersEffect,
    CrisisEffect,
    ExtraReinforcementsEffect,
    NoSituationEffect,
    OpenBordersEffect,
    RestEffect,
    SituationEffect,
    SnowEffect,
    TailwindEffect,
)
from pyteg.core.situaciones.model import (
    NoSituationCard,
    SituationCard,
    SituationContext,
)

if TYPE_CHECKING:
    import random

DEFAULT_SITUATION_RULESET = "none"

_EFFECTS = {
    "none": NoSituationEffect,
    "classic_combat": ClassicCombatEffect,
    "snow": SnowEffect,
    "tailwind": TailwindEffect,
    "crisis": CrisisEffect,
    "extra_reinforcements": ExtraReinforcementsEffect,
    "open_borders": OpenBordersEffect,
    "closed_borders": ClosedBordersEffect,
}

_REST_COLORS = (
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ffff00",
    "#00ffff",
    "#ff00ff",
)


def available_situation_rulesets() -> tuple[str, ...]:
    """Devuelve los rulesets de situaciones disponibles.

    Returns:
        Identificadores aceptados por la fábrica.

    """
    return (DEFAULT_SITUATION_RULESET, "revancha")


def build_situation_deck(
    ruleset: str = DEFAULT_SITUATION_RULESET,
    *,
    rng: random.Random | random.SystemRandom | None = None,
) -> SituationDeck:
    """Construye un mazo para un ruleset explícito.

    Returns:
        Mazo nuevo, mezclado con la fuente indicada.

    Raises:
        ValueError: Si el ruleset no está registrado.

    """
    normalized = ruleset.strip().lower()
    if normalized == DEFAULT_SITUATION_RULESET:
        return SituationDeck(rng=rng)
    if normalized != "revancha":
        msg = f"Ruleset de situaciones desconocido: {ruleset}"
        raise ValueError(msg)

    cards: list[SituationCard] = []
    cards.extend(
        SituationCard(
            card_id=f"classic_combat_{index}",
            name="Combate clásico",
            effect_id="classic_combat",
        )
        for index in range(1, 21)
    )
    for effect_id, name in (
        ("snow", "Nieve"),
        ("tailwind", "Viento a favor"),
        ("crisis", "Crisis"),
        ("extra_reinforcements", "Refuerzos extras"),
        ("open_borders", "Fronteras abiertas"),
        ("closed_borders", "Fronteras cerradas"),
    ):
        cards.extend(
            SituationCard(
                card_id=f"{effect_id}_{index}",
                name=name,
                effect_id=effect_id,
            )
            for index in range(1, 5)
        )
    cards.extend(
        SituationCard(
            card_id=f"rest_{index}",
            name="Descanso",
            effect_id="rest",
            parameter=color,
        )
        for index, color in enumerate(_REST_COLORS, start=1)
    )
    return SituationDeck(cards, rng=rng)


def create_effect(card: SituationCard) -> SituationEffect:
    """Crea la estrategia correspondiente a una carta.

    Returns:
        Estrategia que implementa el efecto de la carta.

    Raises:
        ValueError: Si faltan parámetros o el efecto no está registrado.

    """
    if card.effect_id == "rest":
        if not card.parameter:
            msg = f"La carta {card.card_id} requiere un color"
            raise ValueError(msg)
        return RestEffect(card.parameter)
    effect_type = _EFFECTS.get(card.effect_id)
    if effect_type is None:
        msg = f"Efecto de situación desconocido: {card.effect_id}"
        raise ValueError(msg)
    return effect_type()


def card_is_applicable(card: SituationCard, context: SituationContext) -> bool:
    """Comprueba si una carta puede revelarse con los jugadores actuales.

    Returns:
        ``True`` cuando el efecto es compatible con el contexto.

    """
    return create_effect(card).is_applicable(context)


def no_situation_card(round_number: int) -> dict[str, str | int | None]:
    """Construye el payload público de la ausencia de mazo.

    Returns:
        Diccionario serializable con la carta nula.

    """
    return NoSituationCard().to_public_dict(round_number)
