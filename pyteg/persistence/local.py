"""Partidas de un humano contra bots, sin red ni archivos de entrega."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast

from pyteg.client.bot_strategies import DEFAULT_BOT_DIFFICULTY, BotStrategyFactory
from pyteg.client.event_processor import ClientEventProcessor
from pyteg.client.state_model import ClientStateModel
from pyteg.persistence.archive import make_archive, validate_archive
from pyteg.persistence.in_process import InProcessGame
from pyteg.protocol_validation import validate_server_command
from pyteg.server.hosting.engine import ServerEngine
from pyteg.toml_reader import TomlReader

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.client.bot_strategies import BotStrategy
    from pyteg.persistence.archive import ArchiveRepository
    from pyteg.server.app import Server

_MAX_BOTS = 7
_MAX_NAME = 80


class LocalGame(InProcessGame):
    """Ejecuta una acción de bot a la vez mediante el protocolo habitual."""

    def __init__(
        self,
        server: Server,
        user_id: int,
        *,
        difficulty: str = DEFAULT_BOT_DIFFICULTY,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> None:
        """Prepara una proyección privada independiente para cada bot."""
        super().__init__(server, user_id, receive=receive, repository=repository)
        self.bot_ids: list[int] = []
        self._models: dict[int, ClientStateModel] = {}
        self._processors: dict[int, ClientEventProcessor] = {}
        self.difficulty = BotStrategyFactory.normalize(difficulty)
        self._strategy_factory = BotStrategyFactory()
        self._strategies: dict[int, BotStrategy] = {}
        self._remaining: int | None = None
        self.server.asynchronous = False

    @classmethod
    def create(  # noqa: PLR0913 -- parámetros de creación compartidos.
        cls,
        theme: str,
        name: str,
        bots: int = 3,
        *,
        difficulty: str = DEFAULT_BOT_DIFFICULTY,
        rules_profile: str | None = None,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> LocalGame:
        """Crea de uno a ocho jugadores, incluido el humano.

        Returns:
            Lobby local con bots listos para recibir sus propios eventos.

        Raises:
            ValueError: Si el nombre o la cantidad de bots son inválidos.

        """
        if (
            not name.strip()
            or len(name) > _MAX_NAME
            or type(bots) is not int
            or not 0 <= bots <= _MAX_BOTS
        ):
            msg = "Elegí un nombre y entre cero y siete bots"
            raise ValueError(msg)
        difficulty = BotStrategyFactory.normalize(difficulty)
        session = cls(
            ServerEngine().create(theme, rules_profile),
            1,
            difficulty=difficulty,
            receive=receive,
            repository=repository,
        )
        try:
            session._setup_bots(list(range(2, bots + 2)))
            bot_names = [f"Bot {number}" for number in range(1, bots + 1)]
            bot_names = [
                f"{username} (bot)" if username == name.strip() else username
                for username in bot_names
            ]
            for user_id, username in enumerate([name.strip(), *bot_names], 1):
                if not session.server.registrar_cliente(
                    user_id, session._player(user_id, username)
                ):
                    msg = "No se pudo registrar al jugador local"
                    raise ValueError(msg)  # noqa: TRY301
            session.save_draft()
        except Exception:
            session.server.detener()
            raise
        return session

    @classmethod
    def open(
        cls,
        archive: dict[str, Any],
        *,
        receive: Callable[[int, dict[str, Any]], None] | None = None,
        repository: ArchiveRepository | None = None,
    ) -> LocalGame:
        """Restaura identidades y bots sin convertir el guardado en una sala LAN.

        Returns:
            Partida local restaurada y todavía sin reloj hasta conectar Qt.

        Raises:
            ValueError: Si el modo o las identidades no son válidos.

        """
        archive = validate_archive(archive, kind="game")
        payload = archive["payload"]
        metadata = payload.get("local")
        if (
            not isinstance(metadata, dict)
            or type(metadata.get("userid")) is not int
            or not isinstance(metadata.get("bots"), list)
        ):
            msg = "Guardado local inválido"
            raise ValueError(msg)
        if not isinstance(payload.get("checkpoint"), dict) or not isinstance(
            metadata.get("strategies", {}), dict
        ):
            msg = "Configuración local incompatible"
            raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
        difficulty = BotStrategyFactory.normalize(metadata.get("difficulty", "basic"))
        bot_ids = metadata["bots"]
        if (
            len(bot_ids) > _MAX_BOTS
            or any(type(item) is not int or item <= 0 for item in bot_ids)
            or len(set(bot_ids)) != len(bot_ids)
            or metadata["userid"] in bot_ids
        ):
            msg = "Identidades de bots inválidas"
            raise ValueError(msg)
        session = cls(
            ServerEngine().restore(payload["checkpoint"]),
            metadata["userid"],
            difficulty=difficulty,
            receive=receive,
            repository=repository,
        )
        session._remaining = payload["checkpoint"].get("remaining")
        try:
            session._setup_bots(bot_ids)
            session._restore_players()
            historical = {player.userid() for player in session.server.dame_clientes()}
            if historical != {session.user_id, *bot_ids}:
                msg = "Los bots no corresponden a los jugadores guardados"
                raise ValueError(msg)  # noqa: TRY301
            session._restore_strategies(metadata)
            session.save_draft()
        except Exception:
            session.server.detener()
            raise
        return session

    def _restore_strategies(self, metadata: dict[str, Any]) -> None:
        for user_id in self.bot_ids:
            state = metadata.get("strategies", {}).get(str(user_id))
            if state is not None:
                if not isinstance(state, dict):
                    msg = "Decisiones del bot inválidas"
                    raise ValueError(msg)
                self._strategies[user_id].restore_state(state)
                for command in state["pending"]:
                    validate_server_command(command)
                    if command["mensaje"] not in {
                        "mover_unidad",
                        "reclamar_tarjeta",
                    }:
                        msg = "Acción pendiente del bot inválida"
                        raise ValueError(msg)

    def _setup_bots(self, bot_ids: list[int]) -> None:
        self.bot_ids = list(bot_ids)
        reader = TomlReader.from_theme(self.server.theme)
        for user_id in bot_ids:
            model = ClientStateModel(local_userid=user_id)
            self._models[user_id] = model
            self._processors[user_id] = ClientEventProcessor(model)
            self._strategies[user_id] = self._strategy_factory.create(
                self.difficulty, reader
            )

    def _on_event(self, user_id: int, event: dict[str, Any]) -> None:
        super()._on_event(user_id, event)
        if user_id in self._processors:
            self._processors[user_id].process(event)

    def sync_local(self) -> None:
        """Reconstruye todas las proyecciones antes de dejar jugar a los bots."""
        super().sync_local()
        for user_id in self.bot_ids:
            self.sync_player(user_id)
        self.server.resume_clock(self._remaining)
        self._remaining = None

    def apply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Envía una acción humana al motor y conserva el resultado.

        Returns:
            Confirmación del motor autoritativo.

        """
        result = self._apply_as(self.user_id, payload)
        self.save_draft()
        return result

    def bot_step(self) -> bool:
        """Ejecuta como máximo una acción del bot cuyo turno está activo.

        Returns:
            True si se intentó una acción, False si debe actuar el humano.

        """
        if self._closed:
            return False
        user_id = self.holder()
        if user_id not in self._models:
            return False
        before = cast(
            "ClientStateModel",
            self.server.serialized(lambda: deepcopy(self._models[user_id])),
        )
        strategy = self._strategies[user_id]
        command = strategy.next_command(before)
        if command is None:
            return False
        result = self._apply_as(user_id, command)
        after = cast(
            "ClientStateModel",
            self.server.serialized(lambda: deepcopy(self._models[user_id])),
        )
        strategy.acknowledge(command, result, before, after)
        self.save_draft()
        return True

    def draft(self) -> dict[str, Any]:
        """Captura estado y configuración de los jugadores automáticos.

        Returns:
            Guardado que conserva el modo local.

        """
        return make_archive(
            "game",
            {
                "checkpoint": self.server.capture_state(),
                "local": {
                    "userid": self.user_id,
                    "bots": self.bot_ids,
                    "difficulty": self.difficulty,
                    "strategies": {
                        str(user_id): strategy.saved_state()
                        for user_id, strategy in self._strategies.items()
                    },
                },
            },
        )
