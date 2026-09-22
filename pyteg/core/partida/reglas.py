"""Perfil de reglas público de un tema.

Los mapas contienen geometría y fronteras; este módulo contiene los valores
que cambian entre ediciones del juego.  El perfil se carga desde
``themes/<tema>/reglas.toml`` y se valida antes de crear el servidor.  Las
reglas se mantienen inmutables durante una partida para que servidor,
clientes y simuladores puedan publicar el mismo contrato.
"""

# Profiles are validated at the boundary; these messages intentionally include
# the offending TOML field to make configuration errors actionable.
# ruff: noqa: TRY003, EM101, EM102

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pyteg.config import (
    CARDS_FOR_EXCHANGE,
    CONTINENTS,
    COUNTRIES_DIVISOR,
    DEFAULT_TURN_SECONDS,
    FIRST_TURNS_NO_ATTACK,
    MAX_CARDS_BEFORE_FORCE_EXCHANGE,
    MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE,
    MIN_GENERAL_UNITS,
    MIN_UNITS_TO_LEAVE,
    MISSILE_DAMAGE_DISTANCE_1,
    MISSILE_DAMAGE_DISTANCE_2,
    MISSILE_DAMAGE_DISTANCE_3,
    MISSILE_MAX_DISTANCE,
    MISSILE_UNIT_COST,
    SPECIAL_EXCHANGE_UNITS,
    VICTORY_ALL_COUNTRIES,
)
from pyteg.utils import get_resource_path


class ThemeRulesError(ValueError):
    """Perfil de reglas inexistente o inválido."""


@dataclass(frozen=True, slots=True)
class ThemeRules:
    """Valores de reglas que forman parte del contrato público del tema."""

    theme: str
    version: int
    turn_seconds: int
    victory_countries: int
    lobby_victory_countries: int
    min_players: int
    max_players: int
    first_turn_units: int
    second_turn_units: int
    first_turns_no_attack: int
    attack_dice_max: int
    defense_dice_max: int
    min_general_units: int
    countries_divisor: int
    continent_bonuses: tuple[tuple[str, int], ...]
    exchange_units: tuple[int, ...]
    exchange_multiplier: int
    special_exchange_units: int
    max_cards_before_force_exchange: int
    min_cards_same_symbol_for_exchange: int
    cards_for_exchange: int
    exchange_tail_from_last: bool
    missiles_enabled: bool
    missile_unit_cost: int
    missile_min_units_to_leave: int
    missile_max_distance: int
    missile_damage_by_distance: tuple[int, ...]
    objectives_enabled: bool
    situation_ruleset: str
    continent_card_exchanges: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def continent_bonus_map(self) -> dict[str, int]:
        """Bonos continentales como diccionario para los cálculos."""
        return dict(self.continent_bonuses)

    @property
    def continent_card_exchange_map(self) -> dict[str, tuple[str, ...]]:
        """Equivalencias de las tarjetas de continente para un canje."""
        return dict(self.continent_card_exchanges)

    def to_public_dict(self) -> dict[str, Any]:
        """Serializa el perfil que pueden consumir clientes y simuladores.

        Returns:
            Diccionario JSON serializable con las reglas activas.

        """
        return {
            "theme": self.theme,
            "version": self.version,
            "turn_seconds": self.turn_seconds,
            "victory_countries": self.victory_countries,
            "lobby_victory_countries": self.lobby_victory_countries,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "first_turn_units": self.first_turn_units,
            "second_turn_units": self.second_turn_units,
            "first_turns_no_attack": self.first_turns_no_attack,
            "attack_dice_max": self.attack_dice_max,
            "defense_dice_max": self.defense_dice_max,
            "min_general_units": self.min_general_units,
            "countries_divisor": self.countries_divisor,
            "continent_bonuses": self.continent_bonus_map,
            "exchange_units": list(self.exchange_units),
            "exchange_multiplier": self.exchange_multiplier,
            "exchange_tail_from_last": self.exchange_tail_from_last,
            "special_exchange_units": self.special_exchange_units,
            "max_cards_before_force_exchange": self.max_cards_before_force_exchange,
            "min_cards_same_symbol_for_exchange": (
                self.min_cards_same_symbol_for_exchange
            ),
            "cards_for_exchange": self.cards_for_exchange,
            "continent_card_exchanges": {
                continent: list(symbols)
                for continent, symbols in self.continent_card_exchanges
            },
            "missiles_enabled": self.missiles_enabled,
            "missile_unit_cost": self.missile_unit_cost,
            "missile_min_units_to_leave": self.missile_min_units_to_leave,
            "missile_max_distance": self.missile_max_distance,
            "missile_damage_by_distance": list(self.missile_damage_by_distance),
            "objectives_enabled": self.objectives_enabled,
            "situation_ruleset": self.situation_ruleset,
        }

    @classmethod
    def defaults(cls, theme: str = "classic") -> ThemeRules:
        """Construye el perfil heredado para temas sin ``reglas.toml``.

        Returns:
            Perfil compatible con las constantes históricas del proyecto.

        """
        return cls(
            theme=theme,
            version=1,
            turn_seconds=DEFAULT_TURN_SECONDS,
            victory_countries=30,
            # El servidor histórico usa 0 en el lobby para indicar todos los
            # países; la interfaz puede enviar explícitamente 30 al iniciar.
            lobby_victory_countries=VICTORY_ALL_COUNTRIES,
            min_players=2,
            max_players=6,
            first_turn_units=6,
            second_turn_units=3,
            first_turns_no_attack=FIRST_TURNS_NO_ATTACK,
            attack_dice_max=3,
            defense_dice_max=2,
            min_general_units=MIN_GENERAL_UNITS,
            countries_divisor=COUNTRIES_DIVISOR,
            continent_bonuses=tuple((spec.map_id, spec.bonus) for spec in CONTINENTS),
            exchange_units=(4, 7),
            exchange_multiplier=5,
            special_exchange_units=SPECIAL_EXCHANGE_UNITS,
            max_cards_before_force_exchange=MAX_CARDS_BEFORE_FORCE_EXCHANGE,
            min_cards_same_symbol_for_exchange=MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE,
            cards_for_exchange=CARDS_FOR_EXCHANGE,
            continent_card_exchanges=(),
            exchange_tail_from_last=False,
            missiles_enabled=False,
            missile_unit_cost=MISSILE_UNIT_COST,
            missile_min_units_to_leave=MIN_UNITS_TO_LEAVE,
            missile_max_distance=MISSILE_MAX_DISTANCE,
            missile_damage_by_distance=(
                MISSILE_DAMAGE_DISTANCE_1,
                MISSILE_DAMAGE_DISTANCE_2,
                MISSILE_DAMAGE_DISTANCE_3,
            ),
            objectives_enabled=False,
            situation_ruleset="none",
        )


def load_theme_rules(theme: str) -> ThemeRules:
    """Carga y valida ``themes/<theme>/reglas.toml``.

    Los temas antiguos sin archivo reciben el perfil compatible heredado. Un
    archivo presente nunca se ignora silenciosamente: cualquier campo inválido
    hace fallar el arranque antes de aceptar clientes.

    Returns:
        Perfil inmutable y validado.

    Raises:
        ThemeRulesError: Si el archivo existe pero no cumple el esquema.

    """
    path = get_resource_path(f"themes/{theme}/reglas.toml")
    if not path.is_file():
        return ThemeRules.defaults(theme)
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ThemeRulesError(f"No se pudo leer {path}: {exc}") from exc
    return _build_rules(theme, raw)


def _build_rules(  # noqa: C901, PLR0914, PLR0915
    theme: str, raw: Mapping[str, Any]
) -> ThemeRules:
    if not isinstance(raw, Mapping):
        raise ThemeRulesError("El perfil de reglas debe ser una tabla TOML")
    base = ThemeRules.defaults(theme)

    def section(name: str) -> Mapping[str, Any]:
        value = raw.get(name, {})
        if not isinstance(value, Mapping):
            raise ThemeRulesError(f"La sección [{name}] debe ser una tabla")
        return value

    meta = section("meta")
    game = section("game")
    reinforcements = section("reinforcements")
    continents = section("continents")
    cards = section("cards")
    missiles = section("missiles")
    options = section("options")
    combat = section("combat")

    version = _positive_int(meta.get("version", base.version), "meta.version")
    turn_seconds = _positive_int(
        game.get("turn_seconds", base.turn_seconds), "game.turn_seconds"
    )
    victory = _nonnegative_int(
        game.get("victory_countries", base.victory_countries),
        "game.victory_countries",
    )
    lobby_victory = _nonnegative_int(
        game.get("lobby_victory_countries", base.lobby_victory_countries),
        "game.lobby_victory_countries",
    )
    min_players = _positive_int(
        game.get("min_players", base.min_players), "game.min_players"
    )
    max_players = _positive_int(
        game.get("max_players", base.max_players), "game.max_players"
    )
    if min_players > max_players:
        raise ThemeRulesError("game.min_players no puede superar max_players")
    first_units = _positive_int(
        game.get("first_turn_units", base.first_turn_units), "game.first_turn_units"
    )
    second_units = _positive_int(
        game.get("second_turn_units", base.second_turn_units), "game.second_turn_units"
    )
    no_attack = _nonnegative_int(
        game.get("first_turns_no_attack", base.first_turns_no_attack),
        "game.first_turns_no_attack",
    )
    attack_dice_max = _positive_int(
        combat.get("attack_dice_max", base.attack_dice_max),
        "combat.attack_dice_max",
    )
    defense_dice_max = _positive_int(
        combat.get("defense_dice_max", base.defense_dice_max),
        "combat.defense_dice_max",
    )
    min_general = _positive_int(
        reinforcements.get("minimum", base.min_general_units),
        "reinforcements.minimum",
    )
    divisor = _positive_int(
        reinforcements.get("countries_divisor", base.countries_divisor),
        "reinforcements.countries_divisor",
    )

    if continents:
        bonus_items: list[tuple[str, int]] = []
        for continent, bonus in continents.items():
            if not isinstance(continent, str) or not continent.strip():
                raise ThemeRulesError("continents contiene un ID inválido")
            bonus_items.append((
                continent,
                _nonnegative_int(bonus, f"continents.{continent}"),
            ))
        continent_bonuses = tuple(bonus_items)
    else:
        continent_bonuses = base.continent_bonuses

    exchange_raw = cards.get("exchange_units", list(base.exchange_units))
    if not isinstance(exchange_raw, list) or not exchange_raw:
        raise ThemeRulesError("cards.exchange_units debe ser una lista no vacía")
    exchange_units = tuple(
        _positive_int(value, "cards.exchange_units") for value in exchange_raw
    )
    exchange_multiplier = _positive_int(
        cards.get("exchange_multiplier", base.exchange_multiplier),
        "cards.exchange_multiplier",
    )
    special_exchange = _positive_int(
        cards.get("special_exchange_units", base.special_exchange_units),
        "cards.special_exchange_units",
    )
    max_cards = _positive_int(
        cards.get("max_before_force_exchange", base.max_cards_before_force_exchange),
        "cards.max_before_force_exchange",
    )
    min_same = _positive_int(
        cards.get("min_same_symbol", base.min_cards_same_symbol_for_exchange),
        "cards.min_same_symbol",
    )
    cards_for_exchange = _positive_int(
        cards.get("cards_for_exchange", base.cards_for_exchange),
        "cards.cards_for_exchange",
    )
    continent_card_exchanges = _parse_continent_card_exchanges(
        cards.get("continent_exchanges", {}),
        "cards.continent_exchanges",
    )
    exchange_tail_from_last = _bool(
        cards.get("exchange_tail_from_last", False),
        "cards.exchange_tail_from_last",
    )

    damage_raw = missiles.get(
        "damage_by_distance", list(base.missile_damage_by_distance)
    )
    if not isinstance(damage_raw, list) or not damage_raw:
        raise ThemeRulesError("missiles.damage_by_distance debe ser una lista no vacía")
    damage = tuple(
        _positive_int(value, "missiles.damage_by_distance") for value in damage_raw
    )
    missile_enabled = _bool(
        missiles.get("enabled", base.missiles_enabled), "missiles.enabled"
    )
    missile_cost = _positive_int(
        missiles.get("unit_cost", base.missile_unit_cost), "missiles.unit_cost"
    )
    missile_leave = _nonnegative_int(
        missiles.get("min_units_to_leave", base.missile_min_units_to_leave),
        "missiles.min_units_to_leave",
    )
    missile_distance = _positive_int(
        missiles.get("max_distance", base.missile_max_distance),
        "missiles.max_distance",
    )
    if missile_distance > len(damage):
        raise ThemeRulesError(
            "missiles.max_distance no puede superar damage_by_distance"
        )

    objectives_enabled = _bool(
        options.get("objectives_enabled", base.objectives_enabled),
        "options.objectives_enabled",
    )
    situation_ruleset = options.get("situation_ruleset", base.situation_ruleset)
    if not isinstance(situation_ruleset, str) or not situation_ruleset.strip():
        raise ThemeRulesError("options.situation_ruleset debe ser texto no vacío")
    situation_ruleset = situation_ruleset.strip().lower()
    if situation_ruleset not in {"none", "revancha"}:
        raise ThemeRulesError(
            f"options.situation_ruleset desconocido: {situation_ruleset}"
        )

    return ThemeRules(
        theme=theme,
        version=version,
        turn_seconds=turn_seconds,
        victory_countries=victory,
        lobby_victory_countries=lobby_victory,
        min_players=min_players,
        max_players=max_players,
        first_turn_units=first_units,
        second_turn_units=second_units,
        first_turns_no_attack=no_attack,
        attack_dice_max=attack_dice_max,
        defense_dice_max=defense_dice_max,
        min_general_units=min_general,
        countries_divisor=divisor,
        continent_bonuses=continent_bonuses,
        exchange_units=exchange_units,
        exchange_multiplier=exchange_multiplier,
        special_exchange_units=special_exchange,
        max_cards_before_force_exchange=max_cards,
        min_cards_same_symbol_for_exchange=min_same,
        cards_for_exchange=cards_for_exchange,
        continent_card_exchanges=continent_card_exchanges,
        exchange_tail_from_last=exchange_tail_from_last,
        missiles_enabled=missile_enabled,
        missile_unit_cost=missile_cost,
        missile_min_units_to_leave=missile_leave,
        missile_max_distance=missile_distance,
        missile_damage_by_distance=damage,
        objectives_enabled=objectives_enabled,
        situation_ruleset=situation_ruleset,
    )


def _parse_continent_card_exchanges(
    value: object, field: str
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Valida las variables que aporta cada tarjeta de continente.

    Returns:
        Equivalencias normalizadas por continente.

    Raises:
        ThemeRulesError: Si la tabla no tiene el formato esperado.

    """
    if not isinstance(value, Mapping):
        raise ThemeRulesError(f"{field} debe ser una tabla")
    parsed: list[tuple[str, tuple[str, ...]]] = []
    for continent, symbols in value.items():
        if not isinstance(continent, str) or not continent.strip():
            raise ThemeRulesError(f"{field} contiene un continente inválido")
        if not isinstance(symbols, list) or any(
            not isinstance(symbol, str) or not symbol.strip() for symbol in symbols
        ):
            raise ThemeRulesError(
                f"{field}.{continent} debe ser una lista de símbolos no vacía"
                " o vacía para un canje completo"
            )
        parsed.append((continent, tuple(symbols)))
    return tuple(parsed)


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ThemeRulesError(f"{field} debe ser un entero positivo")
    return value


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ThemeRulesError(f"{field} debe ser un entero no negativo")
    return value


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ThemeRulesError(f"{field} debe ser booleano")
    return value
