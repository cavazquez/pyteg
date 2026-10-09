"""Estimaciones acotadas de combate y prioridades del objetivo propio."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import ceil
from typing import TYPE_CHECKING, Any

from pyteg.core.combate.batalla import Batalla

if TYPE_CHECKING:
    from pyteg.client.state_model import ClientStateModel
    from pyteg.toml_reader import TomlReader

_DIE_SIDES = 6
_MAX_PLANNING_UNITS = 40
_MAX_PLANNING_DICE = 4
_BASE_DEFENSE_LIMIT = 3
_COLORS = {
    "rojo": (255, 0, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "amarillo": (255, 255, 0),
    "negro": (0, 0, 0),
    "blanco": (255, 255, 255),
    "magenta": (255, 0, 255),
    "cian": (0, 255, 255),
}
_RELATIVE_OFFSETS = {"derecha": 1, "izquierda": -1}
_COUNTRY_PROGRESS_WEIGHT = 6.0
_CONTINENT_PROGRESS_WEIGHT = 12.0
_DESTROY_TARGET_WEIGHT = 12.0
_ISLAND_WEIGHT = 6.0


@lru_cache(maxsize=16)
def _rolls(dice: int) -> Counter[tuple[int, ...]]:
    return Counter(
        tuple(sorted(roll, reverse=True))
        for roll in product(range(1, _DIE_SIDES + 1), repeat=dice)
    )


@lru_cache(maxsize=16)
def _losses(attack: int, defense: int) -> tuple[tuple[int, int, float], ...]:
    outcomes: Counter[tuple[int, int]] = Counter()
    for attacking, attack_count in _rolls(attack).items():
        for defending, defense_count in _rolls(defense).items():
            result = Batalla.ataquen("a", "d", list(attacking), list(defending))
            lost = result["restar"]
            outcomes[lost.count("a"), lost.count("d")] += attack_count * defense_count
    total = _DIE_SIDES ** (attack + defense)
    return tuple((a, d, count / total) for (a, d), count in outcomes.items())


@lru_cache(maxsize=16384)
def _assault(
    units: int, defenders: int, attack_max: int, defense_max: int, effect: str
) -> tuple[float, float]:
    if defenders <= 0:
        return 1.0, float(units)
    if units <= 0:
        return 0.0, 0.0
    attack = min(units, attack_max)
    defense = min(defenders, defense_max, _BASE_DEFENSE_LIMIT)
    attack = min(units, attack + (effect == "tailwind"), _MAX_PLANNING_DICE)
    defense = min(defenders, defense + (effect == "snow"), _MAX_PLANNING_DICE)
    probability = survivors = 0.0
    for lost_attack, lost_defense, chance in _losses(attack, defense):
        won, remaining = _assault(
            units - lost_attack,
            defenders - lost_defense,
            attack_max,
            defense_max,
            effect,
        )
        probability += chance * won
        survivors += chance * remaining
    return probability, survivors


@dataclass(frozen=True)
class CombatEstimate:
    """Probabilidad de conquista y ejército esperado si se conquista."""

    probability: float
    survivors: float


def estimate_conquest(
    model: ClientStateModel, units: int, defenders: int
) -> CombatEstimate:
    """Estima un asalto reservando fuera de él las unidades de defensa.

    Usa el comparador de dados del motor, las reglas públicas y Nieve/Viento
    a favor. Los ejércitos grandes se escalan para acotar el trabajo en Qt.

    Returns:
        Estimación, no un resultado de dados futuros ni una garantía.

    """
    if units <= 0:
        return CombatEstimate(0.0, 0.0)
    rules = model.rules or {}
    scale = max(1.0, max(units, defenders) / _MAX_PLANNING_UNITS)
    probability, remaining = _assault(
        max(0, ceil(units / scale)),
        max(0, ceil(defenders / scale)),
        max(1, min(int(rules.get("attack_dice_max", 3)), _MAX_PLANNING_DICE)),
        max(1, min(int(rules.get("defense_dice_max", 2)), _BASE_DEFENSE_LIMIT)),
        str(model.snapshot.get("situacion", {}).get("efecto", "none")),
    )
    return CombatEstimate(
        probability,
        min(float(units), remaining * scale / probability) if probability else 0.0,
    )


def exclusively_owned(model: ClientStateModel, country: str) -> bool:
    """Consulta propiedad exclusiva sin mirar el motor autoritativo.

    Returns:
        True si el país cuenta para el objetivo del jugador.

    """
    data = model.snapshot["countries"][country]
    return data.get("userid") == model.local_userid and not data.get("compartido")


@dataclass(frozen=True)
class BotObjective:
    """Interpreta sólo las cartas de objetivo que recibió este bot."""

    reader: TomlReader
    goals: tuple[dict[str, Any], ...]

    @classmethod
    def from_model(cls, reader: TomlReader, model: ClientStateModel) -> BotObjective:
        """Busca las definiciones públicas de los IDs propios, incluidos pares.

        Returns:
            Plan vacío si no hay objetivo secreto activo.

        """
        ids = (model.private_objective or {}).get("objetivo_id", "").split("+")
        return cls(
            reader,
            tuple(
                goal
                for objective_id in ids
                if (goal := reader.get_objetivo_secreto(objective_id)) is not None
            ),
        )

    def minimum_garrison(self) -> int:
        """Conserva las tropas mínimas que exige el objetivo propio.

        Returns:
            Una unidad como mínimo o la cuota declarada por la carta.

        """
        return max(
            (int(goal.get("tropas_minimas", 1)) for goal in self.goals), default=1
        )

    def country_value(self, model: ClientStateModel, country: str) -> float:
        """Puntúa países útiles para continentes, cuotas, islas y eliminación.

        Returns:
            Prioridad relativa a los objetivos privados del jugador.

        """
        owned = [
            name
            for name in model.snapshot["countries"]
            if exclusively_owned(model, name)
        ]
        return sum(self._goal_value(goal, model, country, owned) for goal in self.goals)

    def _goal_value(
        self,
        goal: dict[str, Any],
        model: ClientStateModel,
        country: str,
        owned: list[str],
    ) -> float:
        continent = self.reader.continente(country)
        quotas = {
            name: len(self.reader.get_paises(name))
            for name in goal.get("continentes", [])
            if name in self.reader.get_continentes()
        }
        quotas.update(goal.get("cuotas_continentes", {}))
        missing = int(quotas.get(continent, 0)) - sum(
            self.reader.continente(name) == continent for name in owned
        )
        value = _CONTINENT_PROGRESS_WEIGHT / missing if missing > 0 else 0.0
        target = self._target_player(goal, model)
        countries_required = int(goal.get("cantidad_paises", 0))
        if goal.get("tipo") == "destruir_jugador" and target is None:
            countries_required = int(goal.get("paises_alternativos", 24))
        countries_missing = countries_required - sum(
            model.snapshot["countries"][name]["unidades"]
            >= int(goal.get("tropas_minimas", 1))
            for name in owned
        )
        if countries_missing > 0:
            value += 1.0 + _COUNTRY_PROGRESS_WEIGHT / countries_missing
        if (
            target is not None
            and model.snapshot["countries"][country]["userid"] == target
        ):
            value += _DESTROY_TARGET_WEIGHT
        return value + self._island_value(goal, country, owned)

    def _island_value(
        self, goal: dict[str, Any], country: str, owned: list[str]
    ) -> float:
        islands = set(self.reader.get_objetivos_metadata().get("islas", []))
        own_islands = islands.intersection(owned)
        if country not in islands or not goal.get("islas"):
            return 0.0
        continents = {self.reader.continente(name) for name in own_islands}
        value = _ISLAND_WEIGHT if len(own_islands) < int(goal["islas"]) else 0.0
        if (
            len(continents) < int(goal.get("continentes_minimos_islas", 1))
            and self.reader.continente(country) not in continents
        ):
            value += _ISLAND_WEIGHT
        return value

    @staticmethod
    def _target_player(goal: dict[str, Any], model: ClientStateModel) -> int | None:
        wanted = _COLORS.get(str(goal.get("color_objetivo", "")))
        if wanted is not None:
            for player in model.snapshot.get("players", []):
                color = player.get("color") or {}
                if (
                    player["userid"] != model.local_userid
                    and tuple(color.get(key) for key in ("r", "g", "b")) == wanted
                ):
                    return int(player["userid"])
        order = model.snapshot.get("turn_order", [])
        direction = goal.get("objetivo_relativo") or goal.get("jugador_alternativo")
        if (
            direction in _RELATIVE_OFFSETS
            and model.local_userid in order
            and len(order) > 1
        ):
            position = order.index(model.local_userid) + _RELATIVE_OFFSETS[direction]
            return int(order[position % len(order)])
        return None
