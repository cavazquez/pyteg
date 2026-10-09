"""Historial público con diferencias de estado y navegación por acción o turno."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from pyteg.protocol import map_hash_for_theme
from pyteg.protocol_validation import validate_client_event

_PUBLIC_ACTIONS = frozenset({
    "empezar",
    "empezar_partida",
    "seleccionar_color",
    "set_username",
    "agregar_unidad",
    "mover_unidad",
    "atacar",
    "finalizar_turno",
    "reclamar_tarjeta",
    "canje_especial",
    "canjear_tarjetas",
    "canjear_misil",
    "lanzar_misil",
    "volver_lobby",
})
_CACHED_POSITIONS = 4


class GameHistory:
    """Originador del historial; registra cada transición aceptada una sola vez."""

    def __init__(self) -> None:
        """Comienza sin estado ni registros."""
        self._initial: dict[str, Any] | None = None
        self._latest: dict[str, Any] | None = None
        self._records: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []

    def observe(self, kind: str, data: dict[str, Any]) -> None:
        """Conserva sólo resultados públicos de combate de la transición actual."""
        if kind in {"batalla_resultado", "misil_resultado"}:
            self._events.append({"mensaje": kind, **deepcopy(data)})

    def record(
        self,
        snapshot: dict[str, Any],
        *,
        action: str = "estado",
        user_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Agrega un estado inicial o una diferencia pública de estado."""
        current = deepcopy(snapshot)
        if self._initial is None:
            self._initial = current
            self._latest = deepcopy(current)
            self._events.clear()
            return
        if current == self._latest:
            self._events.clear()
            return
        previous = self._latest or {}
        changes = {
            key: value
            for key, value in current.items()
            if key != "countries" and previous.get(key) != value
        }
        changes["countries"] = {
            name: country
            for name, country in current["countries"].items()
            if previous.get("countries", {}).get(name) != country
        }
        public_payload = {
            key: value
            for key, value in (payload or {}).items()
            if key not in {"command_id", "token", "tarjetas"}
        }
        if action not in _PUBLIC_ACTIONS:
            public_payload = {}
        self._records.append({
            "action": action,
            "userid": user_id,
            "time": datetime.now(UTC).isoformat(),
            "turn": deepcopy(current.get("turno")),
            "payload": public_payload,
            "events": deepcopy(self._events),
            "changes": changes,
        })
        self._latest = current
        self._events.clear()

    def export(self) -> dict[str, Any]:
        """Devuelve un memento que no incluye cartas, tokens ni objetivos secretos.

        Returns:
            Historial portable con snapshot inicial y diferencias.

        """
        return deepcopy({
            "version": 1,
            "initial": self._initial,
            "records": self._records,
        })

    def restore(self, data: dict[str, Any]) -> None:
        """Reemplaza el historial sólo después de validar todos sus estados."""
        replay = Replay(data)
        self._initial = replay.snapshot(0) if replay.count else None
        self._records = deepcopy(data["records"])
        self._latest = replay.snapshot(replay.count - 1) if replay.count else None
        self._events.clear()


class Replay:
    """Reconstructor independiente del motor y de las conexiones."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Valida el historial antes de exponer una repetición.

        Raises:
            ValueError: Si el historial o algún estado reconstruido no es válido.

        """
        if data.get("version") != 1 or not isinstance(data.get("records"), list):
            msg = "Historial incompatible"
            raise ValueError(msg)
        initial = data.get("initial")
        self._initial: dict[str, Any] | None = None
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._turn_indices: list[int] = []
        self.records = deepcopy(data["records"])
        if initial is None and not self.records:
            return
        if not isinstance(initial, dict):
            msg = "Falta el estado inicial del historial"
            raise ValueError(msg)  # noqa: TRY004 -- formato inválido.
        try:
            state = deepcopy(initial)
            self._validate(state)
            theme = state["theme"]
            if theme not in {"classic", "revancha", "test"} or state[
                "map_hash"
            ] != map_hash_for_theme(theme):
                msg = "El mapa de la repetición no es compatible"
                raise ValueError(msg)
            identity = theme, state["map_hash"], set(state["countries"])
            self._initial = deepcopy(state)
            self._cache[0] = deepcopy(state)
            self._turn_indices = [0]
            previous_turn = state.get("turno")
            for index, record in enumerate(self.records, 1):
                if (
                    not isinstance(record.get("action"), str)
                    or not isinstance(record.get("payload", {}), dict)
                    or not isinstance(record.get("events", []), list)
                    or any(
                        not isinstance(event, dict)
                        for event in record.get("events", [])
                    )
                ):
                    msg = "Registro de repetición inválido"
                    raise ValueError(msg)
                changes = record["changes"]
                state["countries"].update(deepcopy(changes.get("countries", {})))
                state.update({
                    key: deepcopy(value)
                    for key, value in changes.items()
                    if key != "countries"
                })
                self._validate(state)
                if (
                    state["theme"],
                    state["map_hash"],
                    set(state["countries"]),
                ) != identity:
                    msg = "La repetición cambia de mapa"
                    raise ValueError(msg)
                if state.get("turno") != previous_turn:
                    self._turn_indices.append(index)
                previous_turn = state.get("turno")
        except (KeyError, TypeError, AttributeError) as error:
            msg = "Historial incompleto"
            raise ValueError(msg) from error

    @staticmethod
    def _validate(snapshot: dict[str, Any]) -> None:
        validate_client_event({"mensaje": "snapshot", **snapshot})

    @property
    def count(self) -> int:
        """Cantidad de posiciones disponibles.

        Returns:
            Número de estados completos reconstruidos.

        """
        return len(self.records) + 1 if self._initial is not None else 0

    def snapshot(self, index: int) -> dict[str, Any]:
        """Obtiene una posición independiente de la repetición.

        Returns:
            Estado público del mapa en esa posición.

        Raises:
            IndexError: Si la posición no existe.

        """
        if not 0 <= index < self.count:
            msg = "Posición fuera de la repetición"
            raise IndexError(msg)
        closest = max(position for position in self._cache if position <= index)
        state = deepcopy(self._cache[closest])
        for record in self.records[closest:index]:
            changes = record["changes"]
            state["countries"].update(deepcopy(changes.get("countries", {})))
            state.update({
                key: deepcopy(value)
                for key, value in changes.items()
                if key != "countries"
            })
        self._cache[index] = deepcopy(state)
        while len(self._cache) > _CACHED_POSITIONS:
            obsolete = next(position for position in self._cache if position != 0)
            del self._cache[obsolete]
        return state

    def turn_indices(self) -> list[int]:
        """Localiza el comienzo de cada turno para saltar entre ellos.

        Returns:
            Índices de las posiciones donde cambia el turno.

        """
        return list(self._turn_indices)
