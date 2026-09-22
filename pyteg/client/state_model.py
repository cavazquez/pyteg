"""Modelo de estado del cliente sin dependencia de Qt.

La conexión Qt puede alimentar este modelo y la GUI consumir sus señales o
adaptadores. Los bots y las pruebas pueden usar exactamente el mismo código.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApplyEventResult:
    """Resultado de aplicar un evento versionado."""

    applied: bool
    duplicate: bool = False
    gap: bool = False


@dataclass
class ClientStateModel:
    """Estado público reconstruido desde snapshots y eventos del servidor."""

    # ``-1`` representa que todavía no se recibió ningún snapshot. La revisión
    # pública cero es válida para el lobby inicial y debe poder aplicarse.
    revision: int = -1
    snapshot: dict[str, Any] = field(default_factory=dict)
    snapshot_version: int | None = None
    command_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_phase: str | None = None
    protocol_version: str | None = None
    theme: str | None = None
    map_hash: str | None = None
    rules: dict[str, Any] | None = None
    handshake_accepted: bool = False
    local_userid: int | None = None
    private_cards: list[dict[str, Any]] = field(default_factory=list)
    private_units: dict[str, int] = field(default_factory=dict)
    private_objective: dict[str, str] | None = None
    session_token: str | None = None
    victory: dict[str, Any] | None = None
    _gap_detected: bool = field(default=False, init=False, repr=False)

    def apply_event(self, event: dict[str, Any]) -> ApplyEventResult:
        """Aplica un evento; ignora duplicados y señala huecos de revisión.

        Returns:
            Resultado que indica si se aplicó, fue duplicado o dejó un hueco.

        """
        kind = event.get("mensaje")
        if not isinstance(kind, str):
            return ApplyEventResult(applied=True)
        if kind == "snapshot":
            return self._apply_snapshot(event)
        if kind == "command_result":
            self._apply_command_result(event)
            return ApplyEventResult(applied=True)
        handlers = {
            "hello": self._apply_hello,
            "hello_ack": self._apply_hello_ack,
            "user_id": self._apply_user_id,
            "reconexion": self._apply_reconnection,
            "session_token": self._apply_session_token,
            "pais": self._update_country,
            "misil_agregado": self._update_country_missiles,
            "estado": self._apply_state,
            "fase": self._apply_phase,
            "turno": self._update_turn,
            "configuracion_partida": self._apply_configuration,
            "actualizar_lista_jugadores": self._update_players,
            "username": self._apply_username,
            "color_asignado": self._apply_assigned_color,
            "unidades_disponibles": self._apply_private_units,
            "tarjetas_jugador": self._apply_private_cards,
            "objetivo_secreto": self._apply_private_objective,
            "victoria": self._apply_victory,
        }.get(kind)
        if callable(handlers):
            handlers(event)
        return ApplyEventResult(applied=True)

    def _apply_snapshot(self, event: dict[str, Any]) -> ApplyEventResult:
        revision = int(event["revision"])
        resync = event.get("resync") is True
        if revision < self.revision or (revision == self.revision and not resync):
            return ApplyEventResult(applied=False, duplicate=True)
        gap = not resync and self.revision >= 0 and revision != self.revision + 1
        self.snapshot = deepcopy({
            key: value for key, value in event.items() if key != "mensaje"
        })
        raw_rules = event.get("reglas")
        self.rules = deepcopy(raw_rules) if isinstance(raw_rules, dict) else None
        self.revision = revision
        self.snapshot_version = int(event["snapshot_version"])
        self.last_phase = event.get("fase")
        if event.get("estado") == "EsperarJugadores":
            # Una revancha comienza con el mismo socket, por lo que el
            # snapshot del lobby también debe retirar los datos privados de la
            # partida anterior si algún evento llegó fuera de orden.
            self.private_cards.clear()
            self.private_units.clear()
            self.private_objective = None
            self.victory = None
        self._gap_detected = False if resync else self._gap_detected or gap
        return ApplyEventResult(applied=True, gap=gap)

    def _apply_hello(self, event: dict[str, Any]) -> None:
        self.protocol_version = str(event["protocol_version"])
        self.theme = str(event["theme"])
        self.map_hash = str(event["map_hash"])

    def _apply_hello_ack(self, event: dict[str, Any]) -> None:
        self.handshake_accepted = bool(event["accepted"])

    def _apply_command_result(self, event: dict[str, Any]) -> None:
        command_id = str(event["command_id"])
        self.command_results[command_id] = deepcopy(event)

    def _apply_user_id(self, event: dict[str, Any]) -> None:
        user_id = event.get("user_id")
        if isinstance(user_id, int) and self.local_userid is None:
            self.local_userid = user_id

    def _apply_reconnection(self, event: dict[str, Any]) -> None:
        user_id = event.get("user_id")
        if isinstance(user_id, int):
            self.local_userid = user_id

    def _apply_session_token(self, event: dict[str, Any]) -> None:
        token = event.get("token")
        user_id = event.get("user_id")
        if isinstance(token, str) and (
            self.local_userid is None or user_id == self.local_userid
        ):
            self.session_token = token

    def _apply_state(self, event: dict[str, Any]) -> None:
        self.snapshot["estado"] = event.get("estado", "")

    def _apply_phase(self, event: dict[str, Any]) -> None:
        self.snapshot["fase"] = event.get("fase")
        self.snapshot["refuerzos_pendientes"] = int(event.get("unidades_pendientes", 0))
        self.last_phase = event.get("fase")

    def _apply_configuration(self, event: dict[str, Any]) -> None:
        self.snapshot["configuracion"] = {
            key: value for key, value in event.items() if key != "mensaje"
        }

    def _apply_username(self, event: dict[str, Any]) -> None:
        self._update_player_field(event, "username")

    def _apply_assigned_color(self, event: dict[str, Any]) -> None:
        self._update_player_field(
            {
                "user_id": event.get("id"),
                "color": {key: event.get(key) for key in ("r", "g", "b")},
            },
            "color",
        )

    def _apply_private_units(self, event: dict[str, Any]) -> None:
        unidades = event.get("unidades")
        if isinstance(unidades, dict):
            self.private_units = {
                str(key): int(value)
                for key, value in unidades.items()
                if isinstance(value, int)
            }

    def _apply_private_cards(self, event: dict[str, Any]) -> None:
        tarjetas = event.get("tarjetas")
        if isinstance(tarjetas, list):
            self.private_cards = deepcopy(tarjetas)

    def _apply_private_objective(self, event: dict[str, Any]) -> None:
        objetivo_id = str(event.get("objetivo_id", ""))
        descripcion = str(event.get("descripcion", ""))
        if not objetivo_id and not descripcion:
            self.private_objective = None
            return
        self.private_objective = {
            "objetivo_id": objetivo_id,
            "descripcion": descripcion,
        }

    def _apply_victory(self, event: dict[str, Any]) -> None:
        self.victory = deepcopy(event)

    def _countries(self) -> dict[str, dict[str, Any]]:
        countries = self.snapshot.setdefault("countries", {})
        if not isinstance(countries, dict):
            countries = {}
            self.snapshot["countries"] = countries
        return countries

    def _update_country(self, event: dict[str, Any]) -> None:
        country = event.get("pais")
        if not isinstance(country, str):
            return
        current = self._countries().setdefault(
            country,
            {"userid": None, "unidades": 0, "misiles": 0},
        )
        if isinstance(current, dict):
            current["userid"] = event.get("userid")
            current["unidades"] = event.get("unidades", 0)
            current.setdefault("misiles", 0)

    def _update_country_missiles(self, event: dict[str, Any]) -> None:
        country = event.get("pais")
        missiles = event.get("cantidad_misiles")
        if not isinstance(country, str) or not isinstance(missiles, int):
            return
        current = self._countries().setdefault(
            country,
            {"userid": None, "unidades": 0, "misiles": 0},
        )
        if isinstance(current, dict):
            current["misiles"] = missiles

    def _update_turn(self, event: dict[str, Any]) -> None:
        self.snapshot["turno"] = {
            "num_turno": int(event.get("num_turno", 0)),
            "num_ronda": int(event.get("num_ronda", 1)),
            "jugador_id": event.get("jugador_actual_id"),
            "jugador_nombre": event.get("jugador_actual_nombre"),
            "jugador_color": event.get("jugador_actual_color"),
        }

    def _players(self) -> list[dict[str, Any]]:
        players = self.snapshot.setdefault("players", [])
        if not isinstance(players, list):
            players = []
            self.snapshot["players"] = players
        return players

    def _update_players(self, event: dict[str, Any]) -> None:
        incoming = event.get("jugadores")
        if not isinstance(incoming, list):
            return
        old = {
            player.get("userid"): player
            for player in self._players()
            if isinstance(player, dict)
        }
        players: list[dict[str, Any]] = []
        for raw in incoming:
            if not isinstance(raw, dict) or not isinstance(raw.get("userid"), int):
                continue
            player = dict(old.get(raw["userid"], {}))
            player.update(deepcopy(raw))
            player.setdefault("username", "")
            player.setdefault("admin", False)
            player.setdefault("connected", True)
            player.setdefault("eliminated", False)
            players.append(player)
        self.snapshot["players"] = players

    def _update_player_field(self, event: dict[str, Any], field: str) -> None:
        user_id = event.get("user_id")
        if not isinstance(user_id, int):
            return
        players = self._players()
        player = next(
            (
                item
                for item in players
                if isinstance(item, dict) and item.get("userid") == user_id
            ),
            None,
        )
        if player is None:
            player = {
                "userid": user_id,
                "username": "",
                "color": None,
                "admin": False,
                "connected": True,
                "eliminated": False,
            }
            players.append(player)
        player[field] = deepcopy(event.get(field))

    def needs_snapshot(self) -> bool:
        """Indica si una aplicación anterior detectó un hueco.

        Returns:
            ``True`` cuando el modelo marcó un hueco pendiente de resincronizar.

        """
        return self._gap_detected
