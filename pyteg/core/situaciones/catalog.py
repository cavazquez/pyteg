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
    from collections.abc import Iterable

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

_REST_VARIANTS = (
    ("#ff0000", "Rojo"),
    ("#00ff00", "Verde"),
    ("#0000ff", "Azul"),
    ("#ffff00", "Amarillo"),
    ("#00ffff", "Cian"),
    ("#ff00ff", "Magenta"),
)

_SITUATION_EFFECTS: tuple[tuple[str, str], ...] = (
    ("classic_combat", "Combate clásico"),
    ("snow", "Nieve"),
    ("tailwind", "Viento a favor"),
    ("crisis", "Crisis"),
    ("extra_reinforcements", "Refuerzos extras"),
    ("open_borders", "Fronteras abiertas"),
    ("closed_borders", "Fronteras cerradas"),
    ("rest", "Descanso"),
)


def _build_card_catalog() -> tuple[tuple[SituationCard, str], ...]:
    """Construye una sola definición para el mazo y sus etiquetas de sala.

    Returns:
        Cada carta física junto a una etiqueta que distingue sus copias.

    """
    entries: list[tuple[SituationCard, str]] = []
    for effect_id, name in _SITUATION_EFFECTS:
        if effect_id == "rest":
            entries.extend(
                (
                    SituationCard(
                        card_id=f"rest_{index}",
                        name=name,
                        effect_id=effect_id,
                        parameter=color,
                    ),
                    f"{name} — {color_name}",
                )
                for index, (color, color_name) in enumerate(_REST_VARIANTS, start=1)
            )
            continue
        copies = 20 if effect_id == "classic_combat" else 4
        entries.extend(
            (
                SituationCard(
                    card_id=f"{effect_id}_{index}",
                    name=name,
                    effect_id=effect_id,
                ),
                f"{name} {index}",
            )
            for index in range(1, copies + 1)
        )
    return tuple(entries)


_SITUATION_CARD_CATALOG = _build_card_catalog()


def available_situation_rulesets() -> tuple[str, ...]:
    """Devuelve los rulesets de situaciones disponibles.

    Returns:
        Identificadores aceptados por la fábrica.

    """
    return (DEFAULT_SITUATION_RULESET, "revancha")


def available_situation_effects() -> tuple[tuple[str, str], ...]:
    """Devuelve los tipos de carta seleccionables y sus nombres visibles.

    Returns:
        Pares ``(effect_id, nombre)`` en el orden del mazo original.

    """
    return _SITUATION_EFFECTS


def available_situation_cards() -> tuple[tuple[str, str, str], ...]:
    """Enumera las cartas físicas con etiquetas e IDs de efecto.

    Returns:
        Tuplas ``(card_id, etiqueta, effect_id)`` en el orden original.

    """
    return tuple(
        (card.card_id, label, card.effect_id) for card, label in _SITUATION_CARD_CATALOG
    )


def _selected_effects(enabled_effects: Iterable[str] | None) -> frozenset[str]:
    known = frozenset(effect_id for effect_id, _name in _SITUATION_EFFECTS)
    if enabled_effects is None:
        return known
    requested = tuple(enabled_effects)
    unknown = sorted({
        str(effect_id)
        for effect_id in requested
        if not isinstance(effect_id, str) or effect_id not in known
    })
    if unknown:
        msg = f"Tipos de situación desconocidos: {', '.join(unknown)}"
        raise ValueError(msg)
    return frozenset(requested)


def _selected_cards(enabled_cards: Iterable[str] | None) -> frozenset[str]:
    known = frozenset(card.card_id for card, _label in _SITUATION_CARD_CATALOG)
    if enabled_cards is None:
        return known
    requested = tuple(enabled_cards)
    unknown = sorted({
        str(card_id)
        for card_id in requested
        if not isinstance(card_id, str) or card_id not in known
    })
    if unknown:
        msg = f"Cartas de situación desconocidas: {', '.join(unknown)}"
        raise ValueError(msg)
    return frozenset(requested)


def build_situation_deck(
    ruleset: str = DEFAULT_SITUATION_RULESET,
    *,
    rng: random.Random | random.SystemRandom | None = None,
    enabled_effects: Iterable[str] | None = None,
    enabled_cards: Iterable[str] | None = None,
) -> SituationDeck:
    """Construye un mazo filtrando tipos o cartas físicas explícitas.

    ``enabled_cards`` tiene prioridad sobre ``enabled_effects`` cuando se
    proporcionan ambos filtros.

    Returns:
        Mazo nuevo, mezclado con la fuente indicada.

    Raises:
        ValueError: Si el ruleset, tipo o carta no está registrado.

    """
    normalized = ruleset.strip().lower()
    if normalized not in available_situation_rulesets():
        msg = f"Ruleset de situaciones desconocido: {ruleset}"
        raise ValueError(msg)
    selected_effects = _selected_effects(enabled_effects)
    selected_cards = _selected_cards(enabled_cards)
    if normalized == DEFAULT_SITUATION_RULESET:
        return SituationDeck(rng=rng)
    cards = [
        card
        for card, _label in _SITUATION_CARD_CATALOG
        if (
            card.card_id in selected_cards
            if enabled_cards is not None
            else card.effect_id in selected_effects
        )
    ]
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
