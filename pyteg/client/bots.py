"""Decisiones de bots basadas en el mapa público y su propia mano."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from itertools import combinations
from operator import itemgetter
from typing import TYPE_CHECKING, Any

from pyteg.core.cartas.canje import seleccion_valida
from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pyteg.client.state_model import ClientStateModel
    from pyteg.toml_reader import TomlReader

_DEFAULT_EXCHANGE_SIZE = 3
_MAX_ACTIONS = 256
_TURN_KEY_SIZE = 2


def choose_exchange(
    cards: list[dict[str, Any]],
    count: int = _DEFAULT_EXCHANGE_SIZE,
    *,
    equivalences: Mapping[str, Sequence[str]] | None = None,
) -> list[dict[str, str]]:
    """Selecciona un canje con las mismas equivalencias que usa el motor.

    Returns:
        Identificadores de cartas válidas para enviar, o una lista vacía.

    """
    candidates = [
        TarjetaDePais(
            card["pais"],
            card["simbolo"],
            tipo=card.get("tipo", "pais"),
            continente=card.get("continente"),
        )
        for card in cards
    ]
    for size in range(1, min(count, len(candidates)) + 1):
        for selection in combinations(candidates, size):
            if seleccion_valida(
                selection, equivalencias=equivalences, cantidad_variables=count
            ):
                return [
                    {"pais": card.pais, "simbolo": card.simbolo} for card in selection
                ]
    return []


def shortest_distance(adjacency: dict[str, list[str]], origin: str, target: str) -> int:
    """Calcula distancia usando solamente las fronteras públicas.

    Returns:
        Saltos entre países o -1 si no existe un camino.

    """
    queue = deque([(origin, 0)])
    visited = {origin}
    while queue:
        country, distance = queue.popleft()
        if country == target:
            return distance
        for neighbor in adjacency.get(country, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return -1


def is_frontier(
    adjacency: dict[str, list[str]],
    owners: dict[str, int | None],
    user_id: int,
    country: str,
) -> bool:
    """Indica si un país propio limita con un enemigo.

    Returns:
        True si hay una frontera enemiga.

    """
    return any(owners.get(neighbor) != user_id for neighbor in adjacency[country])


@dataclass
class BasicBotStrategy:
    """Refuerza fronteras, ataca con ventaja y usa cartas y misiles."""

    reader: TomlReader
    turn_key: tuple[int, int] | None = None
    actions: int = 0
    attempted: set[str] = field(default_factory=set)
    pending: list[dict[str, Any]] = field(default_factory=list)

    def next_command(self, model: ClientStateModel) -> dict[str, Any] | None:
        """Decide una única acción para permitir que Qt siga respondiendo.

        Returns:
            Comando normal del protocolo, o None fuera del turno.

        """
        snapshot = model.snapshot
        turn = snapshot.get("turno")
        if (
            snapshot.get("estado") != "JUGANDO"
            or not isinstance(turn, dict)
            or turn.get("jugador_id") != model.local_userid
        ):
            return None
        key = (int(turn["num_ronda"]), int(turn["num_turno"]))
        if key != self.turn_key:
            self.turn_key, self.actions = key, 0
            self.attempted.clear()
            self.pending.clear()
        command = self._choose(model)
        if command is not None:
            self.actions += 1
        return command

    def _choose(self, model: ClientStateModel) -> dict[str, Any]:
        if model.snapshot.get("fase") == "colocacion":
            return self._placement(model)
        while self.pending:
            command = self.pending.pop(0)
            if self._fresh(command):
                return command
        if self.actions < _MAX_ACTIONS:
            for choose in (self._launch_missile, self._attack, self._exchange_missile):
                candidate = choose(model)
                if candidate is not None and self._fresh(candidate):
                    return candidate
        return {"mensaje": "finalizar_turno"}

    def _placement(self, model: ClientStateModel) -> dict[str, Any]:
        countries = model.snapshot["countries"]
        for card in model.private_cards:
            country = card["pais"]
            command = {"mensaje": "canje_especial", "pais": country}
            if self._own_units(model, country) and self._fresh(command):
                return command
        count = int(
            (model.rules or {}).get("cards_for_exchange", _DEFAULT_EXCHANGE_SIZE)
        )
        cards = choose_exchange(
            model.private_cards,
            count,
            equivalences=(model.rules or {}).get("continent_card_exchanges", {}),
        )
        command = {"mensaje": "canjear_tarjetas", "tarjetas": cards}
        if cards and self._fresh(command):
            return command
        blocks = model.snapshot.get("bloqueos", [])
        options = [
            country
            for country in countries
            if self._own_units(model, country) > 0
            and self._available(model, country) > 0
            and not any(
                block.get("pais") == country
                and block.get("jugador") == model.local_userid
                for block in blocks
            )
        ]
        if options:
            owners = {name: data.get("userid") for name, data in countries.items()}
            country = max(
                sorted(options),
                key=lambda name: (
                    is_frontier(
                        self.reader.adyacencias,
                        owners,
                        int(model.local_userid or 0),
                        name,
                    ),
                    self._own_units(model, name),
                ),
            )
            return {
                "mensaje": "agregar_unidad",
                "pais": country,
                "tipo_unidad": "infanteria",
                "cantidad": self._available(model, country),
            }
        return {"mensaje": "finalizar_turno"}

    def _available(self, model: ClientStateModel, country: str) -> int:
        return model.private_units.get("infanteria", 0) + model.private_units.get(
            self.reader.continente(country) or "", 0
        )

    @staticmethod
    def _own_units(model: ClientStateModel, country: str) -> int:
        data = model.snapshot.get("countries", {}).get(country, {})
        if data.get("compartido"):
            return sum(
                int(item["unidades"])
                for item in data.get("ocupantes", [])
                if item["userid"] == model.local_userid
            )
        return (
            int(data.get("unidades", 0))
            if data.get("userid") == model.local_userid
            else 0
        )

    @staticmethod
    def _resting(model: ClientStateModel) -> bool:
        situation = model.snapshot.get("situacion", {})
        if situation.get("efecto") != "rest":
            return False
        for player in model.snapshot.get("players", []):
            if player.get("userid") == model.local_userid and player.get("color"):
                color = player["color"]
                return f"#{color['r']:02x}{color['g']:02x}{color['b']:02x}" == str(
                    situation.get("parametro")
                )
        return False

    def _attack(self, model: ClientStateModel) -> dict[str, Any] | None:
        rules = model.rules or {}
        turn = model.snapshot["turno"]
        first_rounds = int(rules.get("first_turns_no_attack", 2))
        if rules.get("duel_enabled") and len(model.snapshot.get("players", [])) == 2:  # noqa: PLR2004
            first_rounds = 1
        if turn["num_ronda"] <= first_rounds or self._resting(model):
            return None
        countries = model.snapshot["countries"]
        effect = model.snapshot.get("situacion", {}).get("efecto")
        options = []
        for origin in countries:
            units = self._own_units(model, origin)
            if units <= 1:
                continue
            for target in self.reader.adyacencias[origin]:
                data = countries[target]
                same_continent = self.reader.continente(
                    origin
                ) == self.reader.continente(target)
                blocked_border = (effect == "open_borders" and same_continent) or (
                    effect == "closed_borders" and not same_continent
                )
                if (
                    self._own_units(model, target)
                    or data.get("compartido")
                    or units <= data["unidades"]
                    or blocked_border
                ):
                    continue
                command = {
                    "mensaje": "atacar",
                    "origen": origin,
                    "destino": target,
                    "cantidad_unidades": min(
                        int(rules.get("attack_dice_max", 3)), units - 1
                    ),
                }
                if self._fresh(command):
                    options.append((
                        units - data["unidades"],
                        -data["unidades"],
                        origin,
                        target,
                        command,
                    ))
        return max(options, key=itemgetter(slice(4)))[-1] if options else None

    def _exchange_missile(self, model: ClientStateModel) -> dict[str, Any] | None:
        config = model.snapshot.get("configuracion", {})
        if (
            not config.get("misiles_habilitados")
            or "missile_exchange" in self.attempted
        ):
            return None
        rules = model.rules or {}
        cost = int(rules.get("missile_unit_cost", 6))
        leave = max(1, int(rules.get("missile_min_units_to_leave", 1)))
        options = [
            name
            for name in model.snapshot["countries"]
            if self._own_units(model, name) >= cost + leave
        ]
        if not options:
            return None
        country = max(sorted(options), key=lambda name: self._own_units(model, name))
        return {"mensaje": "canjear_misil", "pais": country}

    def _launch_missile(self, model: ClientStateModel) -> dict[str, Any] | None:
        if not model.snapshot.get("configuracion", {}).get("misiles_habilitados"):
            return None
        rules = model.rules or {}
        countries = model.snapshot["countries"]
        damage = rules.get("missile_damage_by_distance", [])
        options = []
        for origin, data in countries.items():
            if not self._own_units(model, origin) or not data.get("misiles"):
                continue
            for target, enemy in countries.items():
                if (
                    self._own_units(model, target)
                    or enemy.get("compartido")
                    or not enemy.get("unidades")
                ):
                    continue
                distance = shortest_distance(self.reader.adyacencias, origin, target)
                if (
                    1
                    <= distance
                    <= min(int(rules.get("missile_max_distance", 3)), len(damage))
                ):
                    required = damage[distance - 1] + int(
                        rules.get("missile_min_units_to_leave", 1)
                    )
                    if (
                        enemy["unidades"] < required
                        or enemy.get("misiles", 0) >= data["misiles"]
                    ):
                        continue
                    command = {
                        "mensaje": "lanzar_misil",
                        "pais_origen": origin,
                        "pais_destino": target,
                    }
                    if self._fresh(command):
                        options.append((
                            min(enemy["unidades"], damage[distance - 1]),
                            -distance,
                            origin,
                            target,
                            command,
                        ))
        return max(options, key=itemgetter(slice(4)))[-1] if options else None

    def _fresh(self, command: dict[str, Any]) -> bool:
        return json.dumps(command, sort_keys=True) not in self.attempted

    def acknowledge(
        self,
        command: dict[str, Any],
        result: dict[str, Any] | None,
        before: ClientStateModel,
        after: ClientStateModel,
    ) -> None:
        """Evita reintentos infinitos y prepara el movimiento tras conquistar."""
        accepted = result is not None and result.get("accepted") is True
        if not accepted or command["mensaje"] in {"canje_especial", "reclamar_tarjeta"}:
            self.attempted.add(json.dumps(command, sort_keys=True))
        if command["mensaje"] == "canjear_misil":
            self.attempted.add("missile_exchange")
        if accepted and command["mensaje"] == "atacar":
            target = command["destino"]
            if not self._own_units(before, target) and self._own_units(after, target):
                origin = command["origen"]
                amount = self._own_units(after, origin) - 1
                if amount > 0:
                    self.pending.append({
                        "mensaje": "mover_unidad",
                        "origen": origin,
                        "destino": target,
                        "cantidad": amount,
                    })
                self.pending.append({"mensaje": "reclamar_tarjeta"})

    def saved_state(self) -> dict[str, Any]:
        """Conserva decisiones pendientes al guardar a mitad de un turno.

        Returns:
            Datos simples que no contienen información de otros jugadores.

        """
        return {
            "turn": list(self.turn_key) if self.turn_key else None,
            "actions": self.actions,
            "attempted": sorted(self.attempted),
            "pending": self.pending,
        }

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restaura únicamente decisiones con estructura válida.

        Raises:
            ValueError: Si el estado del bot está incompleto o es inválido.

        """
        turn = state.get("turn")
        actions = state.get("actions")
        attempted = state.get("attempted")
        pending = state.get("pending")
        checks = (
            turn is None
            or (
                isinstance(turn, list)
                and len(turn) == _TURN_KEY_SIZE
                and all(type(item) is int and item >= 0 for item in turn)
            ),
            type(actions) is int and actions >= 0,
            isinstance(attempted, list)
            and all(isinstance(item, str) for item in attempted),
            isinstance(pending, list)
            and all(isinstance(item, dict) for item in pending),
        )
        if not all(checks):
            msg = "Decisiones del bot inválidas"
            raise ValueError(msg)
        self.turn_key = tuple(turn) if turn is not None else None
        self.actions = state["actions"]
        self.attempted = set(state["attempted"])
        self.pending = list(state["pending"])
