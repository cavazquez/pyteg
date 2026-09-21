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

This exercises the server protocol, not the Qt GUI/client transport. Chat echoes
act as synchronization barriers because the protocol has no command IDs/acks.
Victory consensus and the server's terminal state are reported separately; use
``--require-finalized`` to make the missing terminal transition fail the run.
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
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

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
    """A buffered TCP peer whose state consists only of received messages."""

    connection: socket.socket
    userid: int = 0
    buffer: bytes = b""
    countries: dict[str, tuple[int, int]] = field(default_factory=dict)
    units: dict[str, int] = field(default_factory=dict)
    turn: dict[str, Any] = field(default_factory=dict)
    victory: dict[str, Any] | None = None
    state: str = ""
    barrier: str = ""
    errors: list[dict[str, Any]] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)
    disconnected: bool = False
    disconnect_turn: int | None = None

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
        self.buffer += data
        result: list[dict[str, Any]] = []
        while b"\0" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\0", 1)
            if len(raw) > MAX_FRAME_BYTES:
                msg = "Oversized server frame"
                raise RuntimeError(msg)
            if not raw:
                continue
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                msg = "Server message is not an object"
                raise TypeError(msg)
            result.append(payload)
            self._apply(payload)
        if len(self.buffer) > MAX_FRAME_BYTES:
            msg = "Unterminated server frame exceeds size limit"
            raise RuntimeError(msg)
        return result

    def _apply(self, data: dict[str, Any]) -> None:
        kind = str(data.get("mensaje", ""))
        self.counts[kind] += 1
        if kind == "user_id" and self.userid == 0:
            # The first ID is ours; subsequent IDs describe other players.
            self.userid = int(data["user_id"])
        elif kind == "pais":
            self.countries[data["pais"]] = (data["userid"], data["unidades"])
        elif kind == "unidades_disponibles":
            self.units = data["unidades"]
        elif kind == "turno":
            self.turn = data
        elif kind == "victoria":
            self.victory = data
        elif kind == "estado":
            self.state = data["estado"]
        elif kind == "chat":
            self.barrier = data["msg"]
        if kind == "error" or data.get("msg_type") == "error":
            self.errors.append(data)


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
        self._disconnect_done = False
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

    def _send(self, bot: Bot, payload: dict[str, Any]) -> None:
        self._record("send", bot, payload)
        frame = json.dumps(payload).encode("utf-8") + b"\0"
        bot.connection.sendall(frame)

    def command(self, bot: Bot, kind: str, **fields: Any) -> None:
        """Send one action and wait until all peers observe its chat barrier.

        Raises:
            RuntimeError: If any client receives a server rule/protocol error.

        """
        self.commands[kind] += 1
        self._send(bot, {"mensaje": kind, **fields})
        marker = f"SIM_BARRIER_{sum(self.commands.values())}"
        self._send(bot, {"mensaje": "chat", "msg": marker})
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

    def _frontier(self, bot: Bot, country: str) -> bool:
        return any(
            bot.countries[neighbor][0] != bot.userid
            for neighbor in self.adjacency[country]
        )

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

    def play(self) -> None:
        """Play until victory, bounded by time and a maximum number of rounds.

        Raises:
            RuntimeError: If no winner is found within the configured round cap.

        """
        admin = self.reference_bot()
        self.command(
            admin,
            "empezar",
            segundos=max(3600, int(self.args.timeout) + 1),
            paises_para_victoria=self.target,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )
        self.command(admin, "empezar_partida")
        while not all(bot.victory for bot in self.connected_bots()):
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
                expected_turn = reference.turn.get("jugador_actual_id")

                def connected_turn_available(
                    expected_turn: Any = expected_turn,
                ) -> bool:
                    return self.has_connected_turn(expected_turn)

                self._wait(
                    connected_turn_available,
                    "a connected player to receive the next turn",
                )
                continue
            self.reinforce(bot)
            if int(turn["num_ronda"]) >= FIRST_COMBAT_ROUND:
                self.attack(bot)
            self.command(bot, "finalizar_turno")
            self.turns_played += 1
            self.disconnect_client()
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
        if controlled < self.target or self.conquests == 0:
            msg = "Victory was not backed by the country target and actual conquest"
            raise RuntimeError(msg)

    def report(self) -> dict[str, Any]:
        """Report outcomes and coverage limits.

        Returns:
            A JSON-serializable account of observed wire state.

        """
        peers = self.connected_bots()
        reference = peers[0] if peers else (self.bots[0] if self.bots else None)
        board = reference.countries if reference is not None else {}
        board_json = json.dumps(board, sort_keys=True).encode("utf-8")
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
            "victory_observed": connected_victories,
            "all_clients_victory_observed": bool(self.bots)
            and all(bot.victory for bot in self.bots),
            "clients": len(self.bots),
            "connected_clients": len(peers),
            "disconnected_clients": [
                {
                    "userid": bot.userid,
                    "client_number": self.bots.index(bot) + 1,
                    "turn": bot.disconnect_turn,
                }
                for bot in self.bots
                if bot.disconnected
            ],
            "countries": self.total_countries,
            "victory_target": self.target,
            "elapsed_seconds": round(time.monotonic() - self.started, 3),
            "turns_played": self.turns_played,
            "last_turn": reference.turn if reference is not None else None,
            "commands": dict(self.commands),
            "conquests": self.conquests,
            "victories": [bot.victory for bot in self.bots],
            "server_states": [bot.state for bot in self.bots],
            "all_clients_finalized": bool(self.bots)
            and all(bot.state == "Finalizado" for bot in self.bots),
            "connected_clients_finalized": connected_finalized,
            "maps_equal": all(bot.countries == board for bot in peers),
            "board_sha256": hashlib.sha256(board_json).hexdigest(),
            "country_counts": ordered_country_counts,
            "final_board": board,
            "received_messages": [dict(bot.counts) for bot in self.bots],
            "errors": [error for bot in self.bots for error in bot.errors],
            "scope": [
                "Production server in a subprocess; actual loopback TCP sockets",
                "Bots buffer NUL frames; Qt client/GUI is not exercised",
                "Sequential commands; no fragmentation/load testing",
                "Optional real TCP client disconnect; remaining players continue",
                "Country victory; secret objectives, cards and missiles unused",
                "Placement, battle, conquest, transfer and turn completion exercised",
                "Chat echoes synchronize commands; no direct server state access",
                "Seeded RNG instrumentation is confined to the child when enabled",
            ],
        }


def _arguments() -> argparse.Namespace:
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
    if args.disconnect_client is not None:
        if not 1 <= args.disconnect_client <= args.clients:
            parser.error("--disconnect-client must identify an existing client")
        if args.disconnect_after_turn <= 0:
            parser.error("--disconnect-after-turn must be positive")
        if args.clients < MIN_DISCONNECT_CLIENTS:
            parser.error("A disconnect scenario requires at least three clients")
    return args


def _server_child(args: argparse.Namespace) -> None:
    from pyteg.server.app import main as server_main  # noqa: PLC0415

    random.seed(args.seed)
    seeded = random.Random(args.seed)  # noqa: S311 -- deterministic simulation only
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
        with patch("secrets.randbelow", seeded.randrange):
            server_main()
    else:
        server_main()


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
                    "victory_observed",
                    "failure",
                    "turns_played",
                    "conquests",
                    "country_counts",
                    "connected_clients",
                    "disconnected_clients",
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
