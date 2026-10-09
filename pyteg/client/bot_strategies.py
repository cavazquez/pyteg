"""Strategy: dificultad intercambiable con ejecución y guardado compartidos."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from math import floor
from operator import itemgetter
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from pyteg.client.bot_planning import BotObjective, estimate_conquest, exclusively_owned
from pyteg.client.bots import BasicBotStrategy, BotAttack, BotMissile, BotMove
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.client.state_model import ClientStateModel
    from pyteg.toml_reader import TomlReader

BOT_DIFFICULTIES = ("easy", "normal", "hard")
DEFAULT_BOT_DIFFICULTY = "normal"
_FRONTIER_WEIGHT = 5.0
_DEFENSE_WEIGHT = 2.0
_ARMY_WEIGHT = 0.1
_STACK_BONUS_LIMIT = 10
_CONTINENT_BREAK_WEIGHT = 5.0
_ATTACK_MARGIN_WEIGHT = 0.5
_MIN_REINFORCEMENT = 2
_OBJECTIVE_WEIGHT = 2.0
_GARRISON_WEIGHT = 15.0
_MIN_CONQUEST_CHANCE = 0.6
_LOOKAHEAD_DISCOUNT = 0.6
_LOOKAHEAD_WIDTH = 4
_LOSS_WEIGHT = 0.5


class BotStrategy(Protocol):
    """Contrato que necesita una partida local, independiente del nivel."""

    def next_command(self, model: ClientStateModel) -> dict[str, Any] | None:
        """Devuelve una acción del jugador o None fuera de su turno."""
        ...

    def acknowledge(
        self,
        command: dict[str, Any],
        result: dict[str, Any] | None,
        before: ClientStateModel,
        after: ClientStateModel,
    ) -> None:
        """Procesa aceptación o rechazo y prepara acciones pendientes."""
        ...

    def saved_state(self) -> dict[str, Any]:
        """Devuelve las decisiones pendientes que se guardan con la partida."""
        ...

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restaura el estado validado de una estrategia."""
        ...


class EasyBotStrategy(BasicBotStrategy):
    """Varía entre jugadas inmediatas sin ponderar continentes u objetivos."""

    def _pick[T](self, model: ClientStateModel, options: list[T]) -> T:
        # El contador ya se guarda: reabrir conserva la elección sin almacenar
        # el estado de un generador ni tocar los dados del motor.
        key = f"{model.local_userid}:{self.turn_key}:{self.actions}"
        number = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8])
        return options[number % len(options)]

    def _select_placement(self, model: ClientStateModel, options: list[str]) -> str:
        return self._pick(model, options)

    def _select_attack(
        self, model: ClientStateModel, options: list[BotAttack]
    ) -> BotAttack | None:
        return self._pick(model, options)

    def _select_missile(
        self, model: ClientStateModel, options: list[BotMissile]
    ) -> BotMissile:
        return self._pick(model, options)

    def _select_missile_exchange(
        self, model: ClientStateModel, options: list[str]
    ) -> str | None:
        return self._pick(model, options)

    def _select_reposition(
        self, model: ClientStateModel, options: list[BotMove]
    ) -> BotMove:
        return self._pick(model, options)


class NormalBotStrategy(BasicBotStrategy):
    """Evalúa fronteras, continentes y la defensa que deja al avanzar."""

    def _threat(
        self, model: ClientStateModel, country: str, exclude: str | None = None
    ) -> int:
        return max(
            (
                int(model.snapshot["countries"][neighbor]["unidades"])
                for neighbor in self.reader.adyacencias[country]
                if neighbor != exclude and not self._own_units(model, neighbor)
            ),
            default=0,
        )

    def _reserve(
        self, model: ClientStateModel, country: str, exclude: str | None = None
    ) -> int:
        return max(
            1,
            min(
                self._own_units(model, country) - 1,
                (self._threat(model, country, exclude) + 1) // 2,
            ),
        )

    def _country_value(self, model: ClientStateModel, country: str) -> float:
        continent = self.reader.continente(country)
        if continent is None:
            return 1.0
        region = self.reader.get_paises(continent)
        owned = sum(exclusively_owned(model, name) for name in region)
        bonus = float(
            (model.rules or {}).get("continent_bonuses", {}).get(continent, 1)
        )
        value = 1.0 + bonus * (owned + 1) / len(region)
        owner = model.snapshot["countries"][country]["userid"]
        if owner != model.local_userid and all(
            model.snapshot["countries"][name]["userid"] == owner
            and not model.snapshot["countries"][name].get("compartido")
            for name in region
        ):
            value += _CONTINENT_BREAK_WEIGHT
        return value

    def _placement_score(self, model: ClientStateModel, country: str) -> float:
        units = self._own_units(model, country)
        threat = self._threat(model, country)
        army = min(units, _STACK_BONUS_LIMIT) * _ARMY_WEIGHT
        if not threat:
            return army
        return (
            _FRONTIER_WEIGHT
            + max(0, threat - units) * _DEFENSE_WEIGHT
            + self._country_value(model, country)
            + army
        )

    def _select_placement(self, model: ClientStateModel, options: list[str]) -> str:
        return max(options, key=lambda name: (self._placement_score(model, name), name))

    def _placement_amount(self, model: ClientStateModel, country: str) -> int:
        need = max(
            _MIN_REINFORCEMENT,
            self._threat(model, country)
            - self._own_units(model, country)
            + _MIN_REINFORCEMENT,
        )
        return min(self._available(model, country), need)

    def _select_attack(
        self, model: ClientStateModel, options: list[BotAttack]
    ) -> BotAttack | None:
        return max(
            options,
            key=lambda option: (
                self._country_value(model, option.target)
                + (option.units - option.defenders) * _ATTACK_MARGIN_WEIGHT
                - self._reserve(model, option.origin, option.target) / option.units,
                option.origin,
                option.target,
            ),
        )

    def _select_missile(
        self, model: ClientStateModel, options: list[BotMissile]
    ) -> BotMissile:
        return max(
            options,
            key=lambda option: (
                option.damage + self._country_value(model, option.target),
                -option.distance,
                option.target,
            ),
        )

    def _select_missile_exchange(
        self, model: ClientStateModel, options: list[str]
    ) -> str | None:
        cost = int((model.rules or {}).get("missile_unit_cost", 6))
        safe = [
            name
            for name in options
            if self._own_units(model, name) - cost >= self._reserve(model, name)
        ]
        return (
            max(
                safe,
                key=lambda name: (
                    self._own_units(model, name) - self._reserve(model, name)
                ),
            )
            if safe
            else None
        )

    def _conquest_move(self, model: ClientStateModel, origin: str, target: str) -> int:
        if not self._threat(model, target):
            return 0
        return max(0, self._own_units(model, origin) - self._reserve(model, origin))

    def _reposition_amount(self, model: ClientStateModel, country: str) -> int:
        return max(0, self._own_units(model, country) - self._reserve(model, country))


class HardBotStrategy(NormalBotStrategy):
    """Combina su objetivo, estimaciones de dados y dos conquistas posibles."""

    def _objective(self, model: ClientStateModel) -> BotObjective:
        return BotObjective.from_model(self.reader, model)

    def _country_value(self, model: ClientStateModel, country: str) -> float:
        return super()._country_value(
            model, country
        ) + _OBJECTIVE_WEIGHT * self._objective(model).country_value(model, country)

    def _reserve(
        self, model: ClientStateModel, country: str, exclude: str | None = None
    ) -> int:
        return max(
            super()._reserve(model, country, exclude),
            self._objective(model).minimum_garrison(),
        )

    def _placement_score(self, model: ClientStateModel, country: str) -> float:
        objective = self._objective(model)
        garrison = max(
            0, objective.minimum_garrison() - self._own_units(model, country)
        )
        neighbors = [
            self._country_value(model, name)
            for name in self.reader.adyacencias[country]
            if not self._own_units(model, name)
            and not self._border_blocked(model, country, name)
        ]
        return (
            super()._placement_score(model, country)
            + garrison * _GARRISON_WEIGHT
            + max(neighbors, default=0.0)
        )

    def _placement_amount(self, model: ClientStateModel, country: str) -> int:
        garrison = self._objective(model).minimum_garrison() - self._own_units(
            model, country
        )
        if garrison > 0:
            return min(self._available(model, country), garrison)
        return super()._placement_amount(model, country)

    def _attack_viable(self, units: int, _defenders: int) -> bool:
        return units > 1

    def _select_attack(
        self, model: ClientStateModel, options: list[BotAttack]
    ) -> BotAttack | None:
        scores = []
        for option in options:
            available = option.units - self._reserve(
                model, option.origin, option.target
            )
            estimate = estimate_conquest(model, available, option.defenders)
            if estimate.probability < _MIN_CONQUEST_CHANCE:
                continue
            value = self._country_value(model, option.target)
            future = self._next_conquest_value(model, option, floor(estimate.survivors))
            lost = max(0.0, available - estimate.survivors)
            score = (
                estimate.probability * (value + _LOOKAHEAD_DISCOUNT * future)
                - lost * _LOSS_WEIGHT
            )
            if score > 0:
                scores.append((score, option.origin, option.target, option))
        return max(scores, key=itemgetter(slice(3)))[-1] if scores else None

    def _next_conquest_value(
        self, model: ClientStateModel, option: BotAttack, survivors: int
    ) -> float:
        after = deepcopy(model)
        after.snapshot["countries"][option.target].update({
            "userid": model.local_userid,
            "unidades": max(1, survivors),
        })
        after.snapshot["countries"][option.origin]["unidades"] = self._reserve(
            model, option.origin, option.target
        )
        targets = [
            name
            for name in self.reader.adyacencias[option.target]
            if not self._own_units(after, name)
            and not after.snapshot["countries"][name].get("compartido")
            and not self._border_blocked(after, option.target, name)
        ]
        targets.sort(key=lambda name: self._country_value(after, name), reverse=True)
        scores = []
        for target in targets[:_LOOKAHEAD_WIDTH]:
            estimate = estimate_conquest(
                after,
                survivors - self._reserve(after, option.target),
                after.snapshot["countries"][target]["unidades"],
            )
            if estimate.probability >= _MIN_CONQUEST_CHANCE:
                scores.append(estimate.probability * self._country_value(after, target))
        return max(scores, default=0.0)

    def _conquest_move(self, model: ClientStateModel, origin: str, target: str) -> int:
        minimum = self._objective(model).minimum_garrison()
        needed = max(0, minimum - self._own_units(model, target))
        available = max(0, self._own_units(model, origin) - minimum)
        return min(
            available, max(needed, super()._conquest_move(model, origin, target))
        )

    def _select_reposition(
        self, model: ClientStateModel, options: list[BotMove]
    ) -> BotMove:
        def value(move: BotMove) -> float:
            targets = (
                self._country_value(model, name)
                for name in self.reader.adyacencias[move.target]
                if not self._own_units(model, name)
            )
            return move.amount * (
                self._country_value(model, move.target) + max(targets, default=0.0)
            )

        return max(
            options,
            key=lambda move: (value(move), -move.distance, move.origin, move.target),
        )


def difficulty_labels() -> dict[str, str]:
    """Devuelve nombres traducidos al idioma vigente.

    Returns:
        Etiquetas de los tres niveles elegibles.

    """
    return {"easy": _("Fácil"), "normal": _("Normal"), "hard": _("Difícil")}


class BotStrategyFactory:
    """Selecciona el objeto de estrategia al crear o restaurar bots."""

    _strategies: ClassVar[dict[str, type[BasicBotStrategy]]] = {
        "easy": EasyBotStrategy,
        "normal": NormalBotStrategy,
        "hard": HardBotStrategy,
    }

    @classmethod
    def normalize(cls, difficulty: str) -> str:
        """Acepta los niveles vigentes y el identificador de guardados antiguos.

        Returns:
            Identificador canónico de dificultad.

        Raises:
            ValueError: Si el archivo o la configuración indica otro nivel.

        """
        if not isinstance(difficulty, str):
            msg = _("Dificultad de bot inválida")
            raise ValueError(msg)  # noqa: TRY004 -- configuración de archivo inválida.
        difficulty = {"basic": DEFAULT_BOT_DIFFICULTY}.get(difficulty, difficulty)
        if difficulty not in cls._strategies:
            msg = _("Dificultad de bot desconocida")
            raise ValueError(msg)
        return difficulty

    def create(self, difficulty: str, reader: TomlReader) -> BotStrategy:
        """Construye la estrategia sin inspeccionar estados privados del motor.

        Returns:
            Objeto que implementa el contrato completo del bot.

        """
        return self._strategies[self.normalize(difficulty)](reader)
