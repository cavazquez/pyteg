"""Play a real TCP game with headless bots and save a wire-level trace.

Run from the repository root::

    uv run python -m scripts.simulate_game --clients 3 --victory 30 --seed 7
    uv run python -m scripts.simulate_game --theme test --clients 2 --victory 2

The server runs in a separate process. Bots only use public JSON/NUL messages;
no game state is read or changed in-process. An explicit seed and the default
deterministic dice make the simulation reproducible. Omitting the seed obtains
one from ``secrets``; ``--random-dice`` restores production-style dice for a
stochastic run. The real server never receives a seed and always uses its
production random sources.

This exercises the server protocol and the shared headless client transport/model,
not QWidget rendering. Chat echoes remain synchronization barriers while command
results and snapshots are recorded. Victory consensus and the server's terminal
state are reported separately; use ``--require-finalized`` to make a missing
terminal transition fail the run. ``--secret-objectives`` also checks private
objective assignment and recovery without exposing objectives in public state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import secrets
import select
import socket
import subprocess  # noqa: S404 -- launches only the local server process
import sys
import time
import tomllib
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from functools import partial
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from pyteg.client.event_processor import ClientEventProcessor
from pyteg.client.state_model import ClientStateModel
from pyteg.codecs_utils import NulDelimitedUtf8Codec
from pyteg.config import (
    CARDS_FOR_EXCHANGE,
    MAX_CARDS_BEFORE_FORCE_EXCHANGE,
    MIN_UNITS_FOR_MISSILE_EXCHANGE,
    MISSILE_DAMAGE_DISTANCE_1,
    MISSILE_DAMAGE_DISTANCE_2,
    MISSILE_DAMAGE_DISTANCE_3,
    MISSILE_MAX_DISTANCE,
)
from pyteg.protocol import PROTOCOL_VERSION, map_hash_for_theme
from pyteg.protocol_validation import MessageValidationError, validate_client_event

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TextIO

ROOT = Path(__file__).resolve().parents[1]
MAX_FRAME_BYTES = 1_000_000
MIN_CLIENTS = 2
MAX_CLIENTS = 6
MIN_DISCONNECT_CLIENTS = 3
FIRST_COMBAT_ROUND = 3


@dataclass
class Bot:
    """A TCP peer backed by the same codec, validator and state model as Qt."""

    connection: socket.socket
    userid: int = 0
    codec: NulDelimitedUtf8Codec = field(
        default_factory=lambda: NulDelimitedUtf8Codec(max_frame_bytes=MAX_FRAME_BYTES)
    )
    state_model: ClientStateModel = field(default_factory=ClientStateModel)
    event_processor: ClientEventProcessor = field(init=False)
    special_exchanges: list[dict[str, Any]] = field(default_factory=list)
    missile_results: list[dict[str, Any]] = field(default_factory=list)
    # A reconnecting peer receives current state, not historical event frames.
    missile_results_consensus_offset: int = 0
    barrier: str = ""
    errors: list[dict[str, Any]] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)
    disconnected: bool = False
    disconnect_turn: int | None = None
    reconnected: bool = False
    resync_requested: bool = False
    received_wire_bytes: int = 0
    received_wire_frames: int = 0
    sent_wire_bytes: int = 0
    sent_wire_frames: int = 0

    def __post_init__(self) -> None:
        """Inicializa el procesador común de eventos del cliente."""
        self.event_processor = ClientEventProcessor(self.state_model)

    @property
    def countries(self) -> dict[str, tuple[int, int]]:
        """Devuelve el tablero público proyectado por el modelo compartido."""
        countries = self.state_model.snapshot.get("countries", {})
        if not isinstance(countries, dict):
            return {}
        result: dict[str, tuple[int, int]] = {}
        for name, raw in countries.items():
            if not isinstance(name, str) or not isinstance(raw, dict):
                continue
            owner = raw.get("userid")
            units = raw.get("unidades")
            if isinstance(owner, int) and isinstance(units, int) and units > 0:
                result[name] = (owner, units)
        return result

    @property
    def units(self) -> dict[str, int]:
        """Devuelve las unidades privadas propias del modelo."""
        return dict(self.state_model.private_units)

    @property
    def cards(self) -> list[dict[str, str]]:
        """Devuelve las tarjetas privadas propias del modelo."""
        return [
            {
                "pais": str(card["pais"]),
                "simbolo": str(card["simbolo"]),
            }
            for card in self.state_model.private_cards
            if isinstance(card, dict)
            and isinstance(card.get("pais"), str)
            and isinstance(card.get("simbolo"), str)
        ]

    @property
    def secret_objective(self) -> dict[str, str] | None:
        """Devuelve el objetivo privado recibido por este cliente."""
        objective = self.state_model.private_objective
        return dict(objective) if objective is not None else None

    @property
    def missiles(self) -> dict[str, int]:
        """Devuelve misiles públicos por país desde el snapshot compartido."""
        countries = self.state_model.snapshot.get("countries", {})
        if not isinstance(countries, dict):
            return {}
        return {
            name: int(raw["misiles"])
            for name, raw in countries.items()
            if isinstance(name, str)
            and isinstance(raw, dict)
            and isinstance(raw.get("misiles"), int)
            and raw["misiles"] > 0
        }

    @property
    def turn(self) -> dict[str, Any]:
        """Devuelve el turno con los nombres de campos históricos del bot."""
        turn = self.state_model.snapshot.get("turno", {})
        if not isinstance(turn, dict):
            return {}
        return {
            "num_turno": turn.get("num_turno", 0),
            "num_ronda": turn.get("num_ronda", 1),
            "jugador_actual_id": turn.get("jugador_id"),
        }

    @property
    def victory(self) -> dict[str, Any] | None:
        """Devuelve la victoria pública observada por el modelo."""
        return self.state_model.victory

    @property
    def state(self) -> str:
        """Devuelve el estado público actual."""
        return str(self.state_model.snapshot.get("estado", ""))

    @property
    def player_ids(self) -> list[int]:
        """Devuelve las identidades públicas del snapshot."""
        players = self.state_model.snapshot.get("players", [])
        return [
            int(player["userid"])
            for player in players
            if isinstance(player, dict) and isinstance(player.get("userid"), int)
        ]

    @property
    def players_initialized(self) -> bool:
        """Indica si el modelo recibió una lista pública de jugadores."""
        return bool(self.player_ids)

    @property
    def session_token(self) -> str | None:
        """Devuelve el token privado de sesión del bot."""
        return self.state_model.session_token

    @property
    def pending_session_token(self) -> str | None:
        """Alias de compatibilidad para el token de la conexión temporal."""
        return self.state_model.session_token

    @property
    def handshake_accepted(self) -> bool:
        """Indica si el handshake fue aceptado por el servidor."""
        return self.state_model.handshake_accepted

    def receive(self) -> list[dict[str, Any]]:
        """Read complete frames, retaining partial bytes across TCP receives.

        Returns:
            Complete JSON objects received in this read.

        Raises:
            RuntimeError: On EOF or an oversized frame.
            TypeError: If a server message is not a JSON object.

        """
        data = self.connection.recv(65536)
        if not data:
            msg = f"Client {self.userid}: unexpected server EOF"
            raise RuntimeError(msg)
        self.received_wire_bytes += len(data)
        frames = self.codec.feed(data)
        self.received_wire_frames += len(frames)
        result: list[dict[str, Any]] = []
        for raw in frames:
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                msg = "Server message is not an object"
                raise TypeError(msg)
            try:
                payload = validate_client_event(payload)
            except MessageValidationError as error:
                msg = f"Invalid server event: {error}"
                raise RuntimeError(msg) from error
            if payload.get("mensaje") == "ping":
                frame = (
                    json.dumps({
                        "mensaje": "pong",
                        "heartbeat_id": payload["heartbeat_id"],
                    }).encode("utf-8")
                    + b"\0"
                )
                self.connection.sendall(frame)
                self.sent_wire_bytes += len(frame)
                self.sent_wire_frames += 1
                continue
            result.append(payload)
            self._apply(payload)
        return result

    def _apply(self, data: dict[str, Any]) -> None:
        kind = str(data.get("mensaje", ""))
        self.counts[kind] += 1
        applied = self.event_processor.process(data)
        if applied.gap:
            self.resync_requested = False
        handlers = {
            "user_id": self._apply_user_id,
            "pais": self._apply_country,
            "unidades_disponibles": self._apply_units,
            "tarjetas_jugador": self._apply_cards,
            "misil_agregado": self._apply_missile,
            "canje_especial": self._apply_special_exchange,
            "resultado_misil": self._apply_missile_result,
            "turno": self._apply_turn,
            "victoria": self._apply_victory,
            "estado": self._apply_state,
            "chat": self._apply_chat,
            "session_token": self._apply_session_token,
            "reconexion": self._apply_reconnection,
            "actualizar_lista_jugadores": self._apply_player_list,
        }
        handler = handlers.get(kind)
        if handler is not None:
            handler(data)
        if kind == "error" or data.get("msg_type") == "error":
            self.errors.append(data)
        if kind == "command_result" and data.get("accepted") is False:
            self.errors.append(data)

    def _apply_user_id(self, data: dict[str, Any]) -> None:
        # The first ID is ours; subsequent IDs describe other players.
        if self.userid == 0:
            self.userid = int(data["user_id"])

    def _apply_country(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_units(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_cards(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_missile(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_special_exchange(self, data: dict[str, Any]) -> None:
        self.special_exchanges.append(data)

    def _apply_missile_result(self, data: dict[str, Any]) -> None:
        self.missile_results.append(data)

    def _apply_turn(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_victory(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_state(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_chat(self, data: dict[str, Any]) -> None:
        self.barrier = data["msg"]

    def _apply_session_token(self, data: dict[str, Any]) -> None:
        _ = data

    def _apply_reconnection(self, data: dict[str, Any]) -> None:
        self.userid = int(data["user_id"])
        self.reconnected = True

    def _apply_player_list(self, data: dict[str, Any]) -> None:
        _ = data


class Simulation:
    """Run bounded bot turns against the production server over loopback TCP."""

    def __init__(self, args: argparse.Namespace, trace: TextIO) -> None:
        """Load public map metadata and initialize the run's wire ledger.

        Raises:
            ValueError: If player count or victory target exceed map capacity.

        """
        self.args = args
        self.trace = trace
        self.bots: list[Bot] = []
        self.started = time.monotonic()
        self.deadline = self.started + args.timeout
        self.commands: Counter[str] = Counter()
        self.turns_played = 0
        self.conquests = 0
        self.card_claims = 0
        self.card_exchanges = 0
        self.forced_card_exchanges = 0
        self.special_exchanges = 0
        self.missile_exchanges = 0
        self.missile_launches = 0
        self.reconnections = 0
        self.exercise_cards = bool(args.exercise_cards or args.exercise_exchanges)
        self.exercise_missiles = bool(args.exercise_missiles or args.exercise_exchanges)
        self._disconnect_done = False
        self.port = 0
        theme_dir = ROOT / "themes" / args.theme
        with (theme_dir / "adyacencias.toml").open("rb") as file:
            self.adjacency = tomllib.load(file)["Adyacencias"]
        with (theme_dir / "paises.toml").open("rb") as file:
            countries = tomllib.load(file)
        self.continents = {
            country: str(info["continente"])
            for continent in countries.values()
            for country, info in continent.items()
            if isinstance(info, dict) and "continente" in info
        }
        self.total_countries = len(self.continents)
        self.target = args.victory or self.total_countries
        if args.clients > self.total_countries:
            msg = f"{args.theme} has only {self.total_countries} countries"
            raise ValueError(msg)
        if self.target > self.total_countries:
            msg = "Victory target exceeds the number of countries"
            raise ValueError(msg)

    def _record(self, direction: str, bot: Bot, payload: dict[str, Any]) -> None:
        data = {
            "elapsed": round(time.monotonic() - self.started, 6),
            "direction": direction,
            "client": bot.userid,
            "payload": payload,
        }
        self.trace.write(json.dumps(data, ensure_ascii=False) + "\n")

    def connected_bots(self) -> list[Bot]:
        """Return bots whose TCP connection is still part of the scenario.

        Returns:
            Bots that have not been intentionally disconnected.

        """
        return [bot for bot in self.bots if not bot.disconnected]

    def reference_bot(self) -> Bot:
        """Return a connected bot whose public state can drive the harness.

        Returns:
            The first connected bot.

        Raises:
            RuntimeError: If every configured bot has disconnected.

        """
        try:
            return self.connected_bots()[0]
        except IndexError as error:
            msg = "No connected simulation clients remain"
            raise RuntimeError(msg) from error

    def has_connected_turn(self, user_id: Any) -> bool:
        """Return whether a connected bot owns the advertised turn.

        Returns:
            ``True`` if a connected bot has the given user ID.

        """
        return any(peer.userid == user_id for peer in self.connected_bots())

    def _wait(self, condition: Callable[[], bool], description: str) -> None:
        deadline = min(self.deadline, time.monotonic() + self.args.command_timeout)
        while not condition():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                msg = f"Timed out waiting for {description}"
                raise TimeoutError(msg)
            peers = self.connected_bots()
            if not peers:
                msg = "No connected simulation clients remain"
                raise RuntimeError(msg)
            readable, _, _ = select.select(
                [bot.connection for bot in peers], [], [], min(remaining, 0.1)
            )
            for bot in peers:
                if bot.connection in readable:
                    for payload in bot.receive():
                        self._record("receive", bot, payload)
                        if (
                            bot.state_model.needs_snapshot()
                            and not bot.resync_requested
                        ):
                            bot.resync_requested = True
                            self._send(
                                bot,
                                {
                                    "mensaje": "solicitar_snapshot",
                                    "command_id": uuid.uuid4().hex,
                                },
                            )
                        elif not bot.state_model.needs_snapshot():
                            bot.resync_requested = False

    def _send(self, bot: Bot, payload: dict[str, Any]) -> None:
        self._record("send", bot, payload)
        frame = json.dumps(payload).encode("utf-8") + b"\0"
        bot.connection.sendall(frame)
        bot.sent_wire_bytes += len(frame)
        bot.sent_wire_frames += 1

    def command(self, bot: Bot, kind: str, **fields: Any) -> None:
        """Send one action and wait until all peers observe its chat barrier.

        Raises:
            RuntimeError: If any client receives a server rule/protocol error.

        """
        self.commands[kind] += 1
        command_id = uuid.uuid4().hex
        self._send(bot, {"mensaje": kind, "command_id": command_id, **fields})
        marker = f"SIM_BARRIER_{sum(self.commands.values())}"
        if kind == "reconectar":
            self._wait(
                lambda: bot.reconnected,
                "reconnection confirmation",
            )
        self._send(
            bot,
            {"mensaje": "chat", "command_id": uuid.uuid4().hex, "msg": marker},
        )
        self._wait(
            lambda: (
                all(peer.barrier.endswith(marker) for peer in self.connected_bots())
                or all(peer.victory for peer in self.connected_bots())
            ),
            f"{kind} barrier {marker}",
        )
        errors = [error for peer in self.connected_bots() for error in peer.errors]
        if errors:
            msg = f"Server rejected bot action {kind}: {errors[-1]}"
            raise RuntimeError(msg)
        self.assert_consensus()

    def assert_consensus(self) -> None:
        """Check public board convergence and basic ownership/unit invariants.

        Raises:
            RuntimeError: If peers disagree or the board is malformed.

        """
        peers = self.connected_bots()
        if not peers:
            return
        board = peers[0].countries
        if any(bot.countries != board for bot in peers):
            msg = "Client maps diverged after a command barrier"
            raise RuntimeError(msg)
        missiles = peers[0].missiles
        if any(bot.missiles != missiles for bot in peers):
            msg = "Clients disagree on public missile inventory"
            raise RuntimeError(msg)
        missile_results = peers[0].missile_results[
            peers[0].missile_results_consensus_offset :
        ]
        if any(
            bot.missile_results[bot.missile_results_consensus_offset :]
            != missile_results
            for bot in peers
        ):
            msg = "Clients disagree on missile result events"
            raise RuntimeError(msg)
        if board:
            player_ids = {bot.userid for bot in self.bots}
            if set(board) != set(self.continents) or any(
                owner not in player_ids or units < 1 for owner, units in board.values()
            ):
                msg = "Invalid country ownership, army count, or incomplete board"
                raise RuntimeError(msg)

    def connect(self, port: int, process: subprocess.Popen[bytes]) -> None:
        """Connect actual players; readiness probes must not consume admin ID.

        Raises:
            RuntimeError: If the server process exits during startup.
            TimeoutError: If the server does not listen before timeout.

        """
        self.port = port
        for _ in range(self.args.clients):
            while True:
                if process.poll() is not None:
                    msg = "Server exited during startup; inspect server.log"
                    raise RuntimeError(msg)
                try:
                    connection = socket.create_connection(("127.0.0.1", port), 0.2)
                    break
                except ConnectionRefusedError as error:
                    if time.monotonic() >= self.deadline:
                        msg = "Timed out waiting for server startup"
                        raise TimeoutError(msg) from error
                    time.sleep(0.05)
            connection.settimeout(self.args.command_timeout)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            bot = Bot(connection)
            self.bots.append(bot)
            self._wait(
                lambda: bool(self.bots[-1].userid and self.bots[-1].state),
                "client handshake",
            )
            self.command(
                bot,
                "hello",
                protocol_version=PROTOCOL_VERSION,
                theme=self.args.theme,
                map_hash=map_hash_for_theme(self.args.theme),
                capabilities=[
                    "snapshots",
                    "command_results",
                    "reconnect",
                    "heartbeat",
                ],
                rules=["validated_phases", "one_card_per_turn"],
            )
            self.command(bot, "set_username", username=f"Bot_{bot.userid}")

    def disconnect_client(self) -> None:
        """Close the configured bot connection after a completed turn."""
        client_number = self.args.disconnect_client
        if client_number is None or self._disconnect_done:
            return
        if self.turns_played < self.args.disconnect_after_turn:
            return

        bot = self.bots[client_number - 1]
        bot.disconnected = True
        bot.disconnect_turn = self.turns_played
        self._disconnect_done = True
        self._record(
            "simulation",
            bot,
            {
                "event": "client_disconnected",
                "turn": self.turns_played,
                "userid": bot.userid,
            },
        )
        try:
            bot.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            bot.connection.close()

        if self.args.reconnect_client == client_number:
            self._reconnect_client(bot)

    def _reconnect_client(self, disconnected_bot: Bot) -> None:
        """Reconnect a bot with its saved session token.

        Raises:
            RuntimeError: If the previous connection had no token.
            TimeoutError: If the server does not accept the replacement in time.

        """
        token = disconnected_bot.session_token
        if not token:
            msg = "Disconnected bot did not receive a session token"
            raise RuntimeError(msg)

        old_userid = disconnected_bot.userid
        self._wait(
            lambda: (
                self.reference_bot().players_initialized
                and old_userid not in self.reference_bot().player_ids
            ),
            "server to remove the disconnected player",
        )

        while True:
            if time.monotonic() >= self.deadline:
                msg = "Timed out reconnecting a simulation client"
                raise TimeoutError(msg)
            try:
                connection = socket.create_connection(("127.0.0.1", self.port), 0.2)
                break
            except ConnectionRefusedError, OSError:
                time.sleep(0.05)
        connection.settimeout(self.args.command_timeout)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        active_peers = self.connected_bots()
        # Start a new event-consensus epoch: the replacement does not replay
        # historical missile results, while active peers already have them.
        for peer in active_peers:
            peer.missile_results_consensus_offset = len(peer.missile_results)
        replacement = Bot(connection, userid=old_userid)
        self.bots.append(replacement)
        self._wait(
            lambda: bool(replacement.state and replacement.pending_session_token),
            "reconnection handshake",
        )
        self._send(
            replacement,
            {
                "mensaje": "hello",
                "command_id": uuid.uuid4().hex,
                "protocol_version": PROTOCOL_VERSION,
                "theme": self.args.theme,
                "map_hash": map_hash_for_theme(self.args.theme),
                "capabilities": [
                    "snapshots",
                    "command_results",
                    "reconnect",
                    "heartbeat",
                ],
                "rules": ["validated_phases", "one_card_per_turn"],
            },
        )
        self._wait(
            lambda: replacement.handshake_accepted,
            "reconnection protocol handshake",
        )
        self.command(
            replacement,
            "reconectar",
            user_id=old_userid,
            token=token,
        )
        disconnected_bot.reconnected = True
        self.reconnections += 1
        self._record(
            "simulation",
            replacement,
            {"event": "client_reconnected", "userid": old_userid},
        )

    def _frontier(self, bot: Bot, country: str) -> bool:
        return any(
            bot.countries[neighbor][0] != bot.userid
            for neighbor in self.adjacency[country]
        )

    def sync_cards(self, bot: Bot) -> None:
        """Refresh the active player's private card hand from the server."""
        if self.exercise_cards:
            self.command(bot, "solicitar_tarjetas")

    def claim_card(self, bot: Bot) -> None:
        """Claim the card earned by a conquest and detect forced exchanges.

        Raises:
            RuntimeError: If the server does not update the bot's card hand.

        """
        if not self.exercise_cards or bot.victory:
            return
        cards_before = len(bot.cards)
        self.command(bot, "reclamar_tarjeta")
        self.card_claims += 1
        if len(bot.cards) == cards_before:
            msg = "Card claim did not update the requesting client's hand"
            raise RuntimeError(msg)
        if (
            cards_before >= MAX_CARDS_BEFORE_FORCE_EXCHANGE
            and len(bot.cards) < cards_before
        ):
            self.forced_card_exchanges += 1

    @staticmethod
    def _card_selection(bot: Bot) -> list[dict[str, str]]:
        """Select a valid three-card exchange from a public card snapshot.

        Returns:
            Three cards with one valid symbol combination, or an empty list.

        """
        cards_by_symbol: dict[str, list[dict[str, str]]] = {}
        for card in bot.cards:
            cards_by_symbol.setdefault(card["simbolo"], []).append(card)
        for cards in cards_by_symbol.values():
            if len(cards) >= CARDS_FOR_EXCHANGE:
                return cards[:CARDS_FOR_EXCHANGE]
        distinct: list[dict[str, str]] = []
        seen_symbols: set[str] = set()
        for card in bot.cards:
            if card["simbolo"] not in seen_symbols:
                distinct.append(card)
                seen_symbols.add(card["simbolo"])
        return (
            distinct[:CARDS_FOR_EXCHANGE] if len(distinct) == CARDS_FOR_EXCHANGE else []
        )

    def exchange_cards(self, bot: Bot) -> None:
        """Perform one valid normal card exchange when the hand allows it.

        Raises:
            RuntimeError: If the server does not consume the selected cards.

        """
        if not self.exercise_cards:
            return
        selection = self._card_selection(bot)
        if len(selection) != CARDS_FOR_EXCHANGE:
            return
        cards_before = len(bot.cards)
        self.command(bot, "canjear_tarjetas", tarjetas=selection)
        if len(bot.cards) != cards_before - CARDS_FOR_EXCHANGE:
            msg = "Card exchange did not consume the selected cards"
            raise RuntimeError(msg)
        self.card_exchanges += 1

    def exchange_special_card(self, bot: Bot) -> None:
        """Use a country card matching a country currently owned by the bot.

        Raises:
            RuntimeError: If the server does not consume the country card.

        """
        if not self.exercise_cards:
            return
        matching = [
            card
            for card in bot.cards
            if bot.countries.get(card["pais"], (None, 0))[0] == bot.userid
        ]
        if not matching:
            return
        cards_before = len(bot.cards)
        self.command(bot, "canje_especial", pais=matching[0]["pais"])
        if len(bot.cards) != cards_before - 1:
            msg = "Special exchange did not consume the country card"
            raise RuntimeError(msg)
        self.special_exchanges += 1

    def _distance(self, origin: str, target: str) -> int:
        """Return the public-map shortest path length between two countries.

        Returns:
            Number of adjacency hops, or ``-1`` when no path exists.

        """
        if origin == target:
            return 0
        queue: deque[tuple[str, int]] = deque([(origin, 0)])
        visited = {origin}
        while queue:
            country, distance = queue.popleft()
            for neighbor in self.adjacency[country]:
                if neighbor == target:
                    return distance + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))
        return -1

    @staticmethod
    def _missile_damage(distance: int) -> int:
        """Return the configured damage for a missile distance.

        Returns:
            Configured damage, or zero for a distance outside missile range.

        """
        return {
            1: MISSILE_DAMAGE_DISTANCE_1,
            2: MISSILE_DAMAGE_DISTANCE_2,
            3: MISSILE_DAMAGE_DISTANCE_3,
        }.get(distance, 0)

    def exchange_missile(self, bot: Bot) -> None:
        """Convert six units in one owned country into a missile.

        Raises:
            RuntimeError: If the server does not publish the new missile.

        """
        if not self.exercise_missiles:
            return
        options = [
            (country, units)
            for country, (owner, units) in bot.countries.items()
            if owner == bot.userid and units >= MIN_UNITS_FOR_MISSILE_EXCHANGE
        ]
        if not options:
            return
        country = max(options, key=itemgetter(1, 0))[0]
        missiles_before = bot.missiles.get(country, 0)
        self.command(bot, "canjear_misil", pais=country)
        if bot.missiles.get(country, 0) != missiles_before + 1:
            msg = "Missile exchange did not publish the added missile"
            raise RuntimeError(msg)
        self.missile_exchanges += 1

    def launch_missile(self, bot: Bot) -> None:
        """Launch one available missile at a reachable enemy country.

        Raises:
            RuntimeError: If consumption or the result event is not observed.

        """
        if not self.exercise_missiles:
            return
        options: list[tuple[int, int, str, str]] = []
        for origin, (owner, _) in bot.countries.items():
            if owner != bot.userid or bot.missiles.get(origin, 0) <= 0:
                continue
            for target, (target_owner, target_units) in bot.countries.items():
                if target_owner == bot.userid:
                    continue
                distance = self._distance(origin, target)
                damage = self._missile_damage(distance)
                if 1 <= distance <= MISSILE_MAX_DISTANCE and target_units > damage:
                    options.append((target_units, -distance, origin, target))
        if not options:
            return
        _, _, origin, target = max(options)
        missiles_before = bot.missiles.get(origin, 0)
        results_before = len(bot.missile_results)
        self.command(
            bot,
            "lanzar_misil",
            pais_origen=origin,
            pais_destino=target,
        )
        if bot.missiles.get(origin, 0) != missiles_before - 1:
            msg = "Missile launch did not consume the source missile"
            raise RuntimeError(msg)
        if len(bot.missile_results) != results_before + 1:
            msg = "Missile launch did not publish a result event"
            raise RuntimeError(msg)
        self.missile_launches += 1

    def reinforce(self, bot: Bot) -> None:
        """Spend all available infantry/continent pools on useful owned countries."""
        while True:
            options = [
                country
                for country, (owner, _) in bot.countries.items()
                if owner == bot.userid
                and bot.units.get("infanteria", 0)
                + bot.units.get(self.continents[country], 0)
                > 0
            ]
            if not options:
                return
            country = max(
                sorted(options),
                key=lambda name: (
                    self._frontier(bot, name),
                    bot.countries[name][1],
                ),
            )
            amount = bot.units.get("infanteria", 0) + bot.units.get(
                self.continents[country], 0
            )
            self.command(
                bot,
                "agregar_unidad",
                pais=country,
                tipo_unidad="infanteria",
                cantidad=amount,
            )

    def attack(self, bot: Bot) -> None:
        """Attack favorable adjacent targets and transfer after each conquest."""
        claimed_this_turn = False
        while True:
            options = [
                (country, neighbor)
                for country, (owner, units) in bot.countries.items()
                if owner == bot.userid and units > 1
                for neighbor in self.adjacency[country]
                if bot.countries[neighbor][0] != bot.userid
                and units > bot.countries[neighbor][1]
            ]
            if not options:
                return
            origin, target = max(
                sorted(options),
                key=lambda pair: (
                    bot.countries[pair[0]][1] - bot.countries[pair[1]][1],
                    -bot.countries[pair[1]][1],
                ),
            )
            self.command(
                bot,
                "atacar",
                origen=origin,
                destino=target,
                cantidad_unidades=min(3, bot.countries[origin][1] - 1),
            )
            if bot.countries[target][0] == bot.userid:
                self.conquests += 1
                remaining = bot.countries[origin][1] - 1
                if remaining:
                    self.command(
                        bot,
                        "mover_unidad",
                        origen=origin,
                        destino=target,
                        cantidad=remaining,
                    )
                if not claimed_this_turn:
                    self.claim_card(bot)
                    claimed_this_turn = True

    def _start_game(self) -> None:
        """Start a configured game through the public admin protocol."""
        admin = self.reference_bot()
        self.command(
            admin,
            "empezar",
            segundos=max(3600, int(self.args.timeout) + 1),
            paises_para_victoria=self.target,
            objetivos_secretos=self.args.secret_objectives,
            misiles_habilitados=self.exercise_missiles,
        )
        self.command(admin, "empezar_partida")

    def _turn_bot(self) -> tuple[Bot, dict[str, Any]] | None:
        """Resolve the connected bot that owns the currently advertised turn.

        Returns:
            The active bot and its public turn payload, or ``None`` while waiting
            for a disconnected player's turn to be removed from the rotation.

        Raises:
            RuntimeError: If the round limit is exceeded or no client remains.

        """
        reference = self.reference_bot()
        turn = reference.turn
        if int(turn["num_ronda"]) > self.args.max_rounds:
            msg = "No victory within maximum rounds"
            raise RuntimeError(msg)
        try:
            bot = next(
                peer
                for peer in self.connected_bots()
                if peer.userid == turn["jugador_actual_id"]
            )
        except StopIteration:

            def connected_turn_available() -> bool:
                current_turn = self.reference_bot().turn.get("jugador_actual_id")
                return self.has_connected_turn(current_turn)

            self._wait(
                connected_turn_available,
                "a connected player to receive the next turn",
            )
            return None
        return bot, turn

    def _play_turn(self, bot: Bot, turn: dict[str, Any]) -> None:
        """Execute one bot turn using only the received public messages."""
        self.sync_cards(bot)
        self.exchange_special_card(bot)
        self.exchange_cards(bot)
        self.reinforce(bot)
        self.exchange_missile(bot)
        self.launch_missile(bot)
        if int(turn["num_ronda"]) >= FIRST_COMBAT_ROUND:
            self.attack(bot)
        self.command(bot, "finalizar_turno")
        self.turns_played += 1
        self.disconnect_client()

    def _play_until_victory(self) -> None:
        """Play turns until victory, then validate winner and consensus.

        Raises:
            RuntimeError: If the round limit, winner, or map consensus is invalid.

        """
        while not all(bot.victory for bot in self.connected_bots()):
            selected = self._turn_bot()
            if selected is None:
                continue
            self._play_turn(*selected)

        self._wait(
            lambda: all(
                peer.barrier.endswith(f"SIM_BARRIER_{sum(self.commands.values())}")
                or peer.state == "Finalizado"
                for peer in self.connected_bots()
            ),
            "post-victory barrier or terminal state",
        )
        self.assert_consensus()
        peers = self.connected_bots()
        if any(peer.victory != peers[0].victory for peer in peers):
            msg = "Clients disagree on the winner"
            raise RuntimeError(msg)
        victory = peers[0].victory
        if victory is None:
            msg = "Victory message missing"
            raise RuntimeError(msg)
        winner = victory["ganador_id"]
        controlled = sum(owner == winner for owner, _ in peers[0].countries.values())
        if not self.args.secret_objectives and (
            controlled < self.target or self.conquests == 0
        ):
            msg = "Victory was not backed by the country target and actual conquest"
            raise RuntimeError(msg)

    def _validate_exercise_coverage(self) -> None:
        """Fail a requested exercise mode when its wire action never occurred.

        Raises:
            RuntimeError: If a requested exchange action was not observed.

        """
        if self.exercise_cards and self.card_claims == 0:
            msg = "Card exercise requested but no card was claimed"
            raise RuntimeError(msg)
        if self.exercise_cards and self.card_exchanges == 0:
            msg = "Card exercise requested but no normal exchange was observed"
            raise RuntimeError(msg)
        if self.exercise_missiles and self.missile_exchanges == 0:
            msg = "Missile exercise requested but no missile was exchanged"
            raise RuntimeError(msg)
        if self.exercise_missiles and self.missile_launches == 0:
            msg = "Missile exercise requested but no missile was launched"
            raise RuntimeError(msg)
        if self.args.secret_objectives:
            latest_by_id = {bot.userid: bot for bot in self.bots}
            objectives = {
                userid: bot.secret_objective for userid, bot in latest_by_id.items()
            }
            missing = [
                userid for userid, objective in objectives.items() if objective is None
            ]
            if missing:
                msg = f"Secret objective missing for clients: {missing}"
                raise RuntimeError(msg)
            objective_ids = {
                objective["objetivo_id"]
                for objective in objectives.values()
                if objective is not None
            }
            if len(objective_ids) != len(objectives):
                msg = "Secret objectives leaked or were duplicated between clients"
                raise RuntimeError(msg)

    def play(self) -> None:
        """Play until victory, bounded by time and a maximum number of rounds."""
        self._start_game()
        self._play_until_victory()
        self._validate_exercise_coverage()

    def report(self) -> dict[str, Any]:
        """Report outcomes and coverage limits.

        Returns:
            A JSON-serializable account of observed wire state.

        """
        peers = self.connected_bots()
        reference = peers[0] if peers else (self.bots[0] if self.bots else None)
        board = reference.countries if reference is not None else {}
        board_json = json.dumps(board, sort_keys=True).encode("utf-8")
        received_message_totals: Counter[str] = Counter()
        for bot in self.bots:
            received_message_totals.update(bot.counts)
        latest_by_id = {bot.userid: bot for bot in self.bots}
        identity_bots = list(latest_by_id.values())
        country_counts = Counter({str(bot.userid): 0 for bot in self.bots})
        country_counts.update(str(owner) for owner, _ in board.values())
        ordered_country_counts = dict(
            sorted(country_counts.items(), key=lambda item: (-item[1], int(item[0])))
        )
        connected_victories = bool(peers) and all(bot.victory for bot in peers)
        connected_finalized = bool(peers) and all(
            bot.state == "Finalizado" for bot in peers
        )
        return {
            "theme": self.args.theme,
            "seed": self.args.seed,
            "seed_source": self.args.seed_source,
            "deterministic_dice": self.args.deterministic_dice,
            "secret_objectives": self.args.secret_objectives,
            "victory_observed": connected_victories,
            "all_clients_victory_observed": bool(self.bots)
            and all(bot.victory for bot in identity_bots),
            "clients": len(identity_bots),
            "connected_clients": len(peers),
            "disconnected_clients": [
                {
                    "userid": bot.userid,
                    "client_number": self.bots.index(bot) + 1,
                    "turn": bot.disconnect_turn,
                    "reconnected": bot.reconnected,
                }
                for bot in self.bots
                if bot.disconnected
            ],
            "reconnections": self.reconnections,
            "countries": self.total_countries,
            "victory_target": self.target,
            "elapsed_seconds": round(time.monotonic() - self.started, 3),
            "turns_played": self.turns_played,
            "last_turn": reference.turn if reference is not None else None,
            "commands": dict(self.commands),
            "conquests": self.conquests,
            "card_claims": self.card_claims,
            "card_exchanges": self.card_exchanges,
            "forced_card_exchanges": self.forced_card_exchanges,
            "special_exchanges": self.special_exchanges,
            "missile_exchanges": self.missile_exchanges,
            "missile_launches": self.missile_launches,
            "victories": [bot.victory for bot in self.bots],
            "server_states": [bot.state for bot in self.bots],
            "all_clients_finalized": bool(self.bots)
            and all(bot.state == "Finalizado" for bot in identity_bots),
            "connected_clients_finalized": connected_finalized,
            "maps_equal": all(bot.countries == board for bot in peers),
            "board_sha256": hashlib.sha256(board_json).hexdigest(),
            "country_counts": ordered_country_counts,
            "secret_objective_ids": {
                str(bot.userid): bot.secret_objective["objetivo_id"]
                for bot in identity_bots
                if bot.secret_objective is not None
            },
            "final_board": board,
            "received_messages": [dict(bot.counts) for bot in self.bots],
            "received_message_totals": dict(received_message_totals),
            "country_update_messages": received_message_totals.get("pais", 0),
            "received_wire_bytes": sum(bot.received_wire_bytes for bot in self.bots),
            "received_wire_frames": sum(bot.received_wire_frames for bot in self.bots),
            "sent_wire_bytes": sum(bot.sent_wire_bytes for bot in self.bots),
            "sent_wire_frames": sum(bot.sent_wire_frames for bot in self.bots),
            "errors": [error for bot in self.bots for error in bot.errors],
            "scope": [
                "Production server in a subprocess; actual loopback TCP sockets",
                "Bots buffer NUL frames; Qt client/GUI is not exercised",
                "Sequential commands; no fragmentation/load testing",
                "Optional real TCP client disconnect; remaining players continue",
                "Optional authenticated TCP reconnection with session state sync",
                (
                    "Secret objectives assigned privately and checked after "
                    "reconnection"
                    if self.args.secret_objectives
                    else "Country victory; secret objectives remain unused"
                ),
                "Placement, battle, conquest, transfer and turn completion exercised",
                "Chat echoes synchronize commands; no direct server state access",
                "Seeded RNG instrumentation is confined to the child when enabled",
            ],
        }


def _arguments() -> argparse.Namespace:  # noqa: C901
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("classic", "test"), default="classic")
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed explícita; si se omite se genera con secrets.",
    )
    parser.add_argument("--victory", type=int, default=0, help="0 means all countries")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--command-timeout", type=float, default=10)
    parser.add_argument("--max-rounds", type=int, default=200)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--secret-objectives",
        action="store_true",
        help="Activar objetivos secretos y verificar su entrega privada.",
    )
    dice_group = parser.add_mutually_exclusive_group()
    dice_group.add_argument(
        "--deterministic-dice",
        dest="deterministic_dice",
        action="store_true",
        help="Dados reproducibles para una simulación repetible (predeterminado).",
    )
    dice_group.add_argument(
        "--random-dice",
        dest="deterministic_dice",
        action="store_false",
        help="Dados productivos no reproducibles para una corrida estocástica.",
    )
    parser.set_defaults(deterministic_dice=True)
    parser.add_argument(
        "--disconnect-client",
        type=int,
        help="Número de cliente (1-based) que se desconecta durante la partida.",
    )
    parser.add_argument(
        "--disconnect-after-turn",
        type=int,
        default=0,
        help="Turno completado después del cual se desconecta el cliente.",
    )
    parser.add_argument(
        "--reconnect-client",
        type=int,
        help="Vuelve a conectar este cliente después de desconectarlo.",
    )
    parser.add_argument(
        "--exercise-cards",
        action="store_true",
        help="Reclamar tarjetas y ejecutar canjes normal/especial durante la partida.",
    )
    parser.add_argument(
        "--exercise-missiles",
        action="store_true",
        help="Habilitar misiles y ejecutar canje/lanzamiento durante la partida.",
    )
    parser.add_argument(
        "--exercise-exchanges",
        action="store_true",
        help="Ejercitar todos los canjes: tarjetas, especial y misiles.",
    )
    parser.add_argument("--require-finalized", action="store_true")
    parser.add_argument("--server-child", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not MIN_CLIENTS <= args.clients <= MAX_CLIENTS:
        parser.error("--clients must be between 2 and 6")
    if (
        args.victory < 0
        or min(args.timeout, args.command_timeout, args.max_rounds) <= 0
    ):
        parser.error("Timeouts/rounds must be positive and victory must be nonnegative")
    if args.seed is None:
        args.seed = secrets.randbits(64)
        args.seed_source = "generated_by_secrets"
    else:
        args.seed_source = "explicit"
    if args.disconnect_client is None and args.disconnect_after_turn:
        parser.error("--disconnect-after-turn requires --disconnect-client")
    if args.reconnect_client is not None and args.disconnect_client is None:
        parser.error("--reconnect-client requires --disconnect-client")
    if (
        args.reconnect_client is not None
        and args.reconnect_client != args.disconnect_client
    ):
        parser.error("--reconnect-client must equal --disconnect-client")
    if args.disconnect_client is not None:
        if not 1 <= args.disconnect_client <= args.clients:
            parser.error("--disconnect-client must identify an existing client")
        if args.disconnect_after_turn <= 0:
            parser.error("--disconnect-after-turn must be positive")
        if args.clients < MIN_DISCONNECT_CLIENTS:
            parser.error("A disconnect scenario requires at least three clients")
    return args


def _server_child(args: argparse.Namespace) -> None:
    from pyteg.server.app import Server  # noqa: PLC0415
    from pyteg.server.app import main as server_main  # noqa: PLC0415

    random.seed(args.seed)
    dice_rng = random.Random(args.seed)  # noqa: S311 -- deterministic simulation only
    objective_rng = random.Random(args.seed)  # noqa: S311 -- deterministic simulation only
    server_factory = partial(Server, objective_rng=objective_rng)
    sys.argv = [
        "pyteg-server",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.server_child),
        "--theme",
        args.theme,
        "--quiet",
    ]
    if args.deterministic_dice:
        with patch("secrets.randbelow", dice_rng.randrange):
            server_main(server_factory=server_factory)
    else:
        server_main(server_factory=server_factory)


def main() -> int:
    """Run the simulation, persist evidence, and always clean up sockets/process.

    Returns:
        0 on verified victory; 1 on failure; 2 if strict terminal-state check fails.

    """
    args = _arguments()
    if args.server_child is not None:
        _server_child(args)
        return 0
    output = (
        args.output_dir or ROOT / "logs" / "simulations" / f"{args.theme}-{args.seed}"
    )
    output.mkdir(parents=True, exist_ok=True)
    with (
        (output / "wire.jsonl").open("w", encoding="utf-8") as trace,
        (output / "server.log").open("wb") as server_log,
    ):
        simulation = Simulation(args, trace)
        process: subprocess.Popen[bytes] | None = None
        failure: str | None = None
        try:
            with socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                port = reservation.getsockname()[1]
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--server-child",
                str(port),
                "--theme",
                args.theme,
                "--seed",
                str(args.seed),
            ]
            if args.deterministic_dice:
                command.append("--deterministic-dice")
            else:
                command.append("--random-dice")
            if args.secret_objectives:
                command.append("--secret-objectives")
            environment = dict(
                os.environ,
                PYTHONHASHSEED=str(args.seed % (2**32)),
                PYTHONUNBUFFERED="1",
            )
            process = subprocess.Popen(  # noqa: S603 -- fixed local Python entry point
                command,
                cwd=ROOT,
                env=environment,
                stdout=server_log,
                stderr=subprocess.STDOUT,
            )
            simulation.connect(port, process)
            simulation.play()
        except (OSError, RuntimeError, ValueError, TypeError, StopIteration) as error:
            failure = f"{type(error).__name__}: {error}"
        finally:
            for bot in simulation.bots:
                bot.connection.close()
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        report = simulation.report()
        report["server_process_stopped"] = process is None or process.poll() is not None
        report["failure"] = failure
        report["status"] = "failed" if failure else "victory_verified"
        (output / "result.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "seed",
                    "seed_source",
                    "deterministic_dice",
                    "secret_objectives",
                    "victory_observed",
                    "failure",
                    "turns_played",
                    "conquests",
                    "card_claims",
                    "card_exchanges",
                    "forced_card_exchanges",
                    "special_exchanges",
                    "missile_exchanges",
                    "missile_launches",
                    "country_counts",
                    "connected_clients",
                    "disconnected_clients",
                    "reconnections",
                    "connected_clients_finalized",
                    "all_clients_finalized",
                    "elapsed_seconds",
                )
            },
            indent=2,
        )
    )
    print(f"Evidence: {output.resolve()}")
    if failure:
        return 1
    return (
        2 if args.require_finalized and not report["connected_clients_finalized"] else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
