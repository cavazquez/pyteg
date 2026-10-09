# ruff: noqa: SLF001
"""Memento del estado autoritativo; las conexiones se reconstruyen por separado.

La copia contiene datos privados. Sólo se entrega a participantes que anuncian
la capacidad de hospedar una partida en una red local de confianza.
"""

from __future__ import annotations

import random
from dataclasses import fields, replace
from typing import TYPE_CHECKING, Any, cast

from pyteg.config import CONTINENTS
from pyteg.core.partida.reglas import ThemeRules
from pyteg.core.situaciones.catalog import create_effect
from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.model import SituationContext
from pyteg.core.situaciones.runtime import SituationRuntime
from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from pyteg.persistence.values import capture, pack, restore, unpack
from pyteg.server.conexion.cliente import Client
from pyteg.server.juego.command_executor import GameCommandExecutor
from pyteg.server.juego.game import Game

if TYPE_CHECKING:
    from pyteg.server.app import Server
    from pyteg.server.conexion.connection import ConnectionServer

CHECKPOINT_VERSION = 1
_SERVER = (
    "_state_revision",
    "_admin_user_id",
    "_pending_admin_user_id",
    "_admin_succession_anchor",
    "_admin_excluded_ids",
)
_CONFIG = (
    "_segundos_por_turno",
    "_paises_para_victoria",
    "_objetivos_secretos_activados",
    "_misiles_habilitados",
    "_situation_ruleset",
    "_situation_effects",
    "_situation_card_ids",
)
_OBJECTIVES = (
    "_ids_objetivos_habilitados",
    "objetivos_asignados",
    "objetivos_adicionales",
    "_revancha_players",
)
_GAME = (
    "_start",
    "_finalizada",
    "_solo_mode",
    "_revancha_duel",
    "_eliminados",
    "_desconectados",
    "_reconnect_tokens",
    "_paises_para_victoria",
    "_fase",
)
_TURNS = ("_first_turn_units", "_num_turno", "_num_ronda", "_turno_logico")
_CARDS = (
    "_cant_canjes",
    "_jugadores_pueden_reclamar",
    "_jugadores_reclamaron",
    "_jugadores_canjes_turno",
    "_continentes_pendientes",
)
_SITUATION = ("_active_card", "_state", "_round_number", "_rounds_started")
_TURN_TYPES = {
    "PrimerTurno": PrimerTurno,
    "SegundoTurno": SegundoTurno,
    "SiguientesTurnos": SiguientesTurnos,
}
_TURN_FIELDS = {
    "PrimerTurno": ("_jugador", "_unidades"),
    "SegundoTurno": ("_jugador", "_unidades", "_unidades_calculadas"),
    "SiguientesTurnos": (
        "_jugador",
        "_unidades",
        "_unidades_calculadas",
        "_unidades_continentes",
    ),
}


def prepare_shared_transition(server: Server, seed: int, timestamp: str) -> None:
    """Configura entropía y tiempo de una única transición replicada.

    El transporte proporciona una semilla nueva en cada acuerdo; todos los
    motores ejecutan las reglas con las mismas extracciones y dados.
    """
    rng = random.Random(seed)  # noqa: S311 -- consenso reproducible, sin credenciales.
    server.history.set_record_time(timestamp)
    server.objetivos_secretos._rng = rng
    server._game_coordinator._situation_rng = rng
    server.color.set_random_source(rng)
    server.mapa.set_random_source(rng)
    server.mazo.set_random_source(rng)
    if server.game is not None:
        server.game._dice_rng = rng
        runtime = server.game._situation_runtime
        runtime._deck._rng = rng
        runtime.set_random_source(rng)


class _OfflineConnection:
    """Puerto inerte de un jugador histórico antes de recuperar su socket."""

    def send(self, _data: str) -> None:
        """Descarta notificaciones hasta que el jugador se reconecte."""


def _rng_state(rng: Any) -> Any:
    if rng is None or isinstance(rng, random.SystemRandom):
        return None
    return pack(rng.getstate())


def _restore_rng(state: Any) -> random.Random:
    if state is None:
        return random.SystemRandom()
    rng = random.Random()  # noqa: S311 -- sólo restaura dados reproducibles.
    rng.setstate(unpack(state))
    return rng


def _random_links(server: Server) -> dict[str, str]:
    game = server.game
    runtime = game._situation_runtime if game is not None else None
    sources = {
        "objectives": server.objetivos_secretos._rng,
        "situations": server._game_coordinator._situation_rng,
        "battle": game._dice_rng if game is not None else None,
        "deck": runtime._deck._rng if runtime is not None else None,
        "situation_dice": getattr(runtime._dice_source, "_rng", None)
        if runtime is not None
        else None,
    }
    seen: dict[int, str] = {}
    links = {}
    for label, source in sources.items():
        links[label] = seen.get(id(source), label) if source is not None else label
        if source is not None:
            seen[id(source)] = links[label]
    return links


def _restore_random_sources(checkpoint: dict[str, Any]) -> dict[str, random.Random]:
    game = checkpoint["game"] or {}
    states = {
        "objectives": checkpoint["objective_rng"],
        "situations": checkpoint["situation_rng"],
        "battle": game.get("dice_rng"),
        "deck": game.get("deck_rng"),
        "situation_dice": game.get("situation_dice_rng"),
    }
    sources: dict[str, random.Random] = {}
    for label, state in states.items():
        reference = checkpoint["rng_links"][label]
        if reference == label:
            sources[label] = _restore_rng(state)
        elif reference in sources:
            sources[label] = sources[reference]
        else:
            msg = "Referencia de aleatoriedad inválida en la copia"
            raise ValueError(msg)
    return sources


def export_checkpoint(server: Server) -> dict[str, Any]:
    """Captura una transición completa desde el ejecutor serial del juego.

    Returns:
        Datos completos de una transición, incluidos los datos privados.

    """
    coordinator = server._game_coordinator
    game = server.game
    players = (
        game.jugadores()
        if game is not None
        else list(
            {
                **server.migration_sessions,
                **{
                    client.userid(): client
                    for client in server.dame_clientes()
                    if not client.es_reconexion_pendiente()
                },
            }.values()
        )
    )
    result: dict[str, Any] = {
        "version": CHECKPOINT_VERSION,
        "history": server.history.export(),
        "asynchronous": server.asynchronous,
        "theme": server.theme,
        "map_hash": server.map_hash(),
        "rules": capture(
            server.reglas(), tuple(field.name for field in fields(ThemeRules))
        ),
        "server": capture(server, _SERVER),
        "state": server.estado.estado_actual(),
        "config": capture(coordinator, _CONFIG),
        "objectives": capture(server.objetivos_secretos, _OBJECTIVES),
        "objective_rng": _rng_state(server.objetivos_secretos._rng),
        "situation_rng": _rng_state(coordinator._situation_rng),
        "rng_links": _random_links(server),
        "countries": {
            name: [country.unidades, country.jugador, country.misiles]
            for name, country in server.mapa._mapa.items()
        },
        "shared": pack(server.mapa._condominios),
        "deck": pack(server.mazo.mazo),
        "players": [
            {
                "userid": player.userid(),
                "username": player.username(),
                "color": color.to_hex()
                if (color := player.color_actual()) is not None
                else None,
                "token": player.reconnect_token(),
                "cache": player.export_command_cache(),
            }
            for player in cast("list[Client]", players)
        ],
        "connected": [
            client.userid()
            for client in server.dame_clientes()
            if not client.es_reconexion_pendiente()
        ],
        "game": None,
        "remaining": server.clock_remaining(),
    }
    if game is not None:
        runtime = game._situation_runtime
        result["game"] = {
            "state": capture(game, _GAME),
            "turn_manager": capture(game._turn_manager, _TURNS),
            "first_units": game._turn_manager._turn_factory.first_units,
            "turns": [
                {
                    "type": type(turn).__name__,
                    "state": capture(turn, _TURN_FIELDS[type(turn).__name__]),
                }
                for turn in game.turnos()
            ],
            "cards": capture(game._card_manager, _CARDS),
            "pacts": capture(game.pactos(), ("_pactos", "_next_id")),
            "situation": capture(runtime, _SITUATION),
            "context": {
                "round_number": runtime._context.round_number,
                "player_ids": pack(runtime._context.player_ids),
                "player_colors": pack(dict(runtime._context.player_colors)),
            },
            "situation_deck": capture(runtime._deck, ("_cards", "_discard")),
            "deck_rng": _rng_state(runtime._deck._rng),
            "dice_rng": _rng_state(game._dice_rng),
            "situation_dice_rng": _rng_state(
                getattr(runtime._dice_source, "_rng", None)
            ),
        }
    return result


def restore_checkpoint(server: Server, checkpoint: dict[str, Any]) -> dict[int, Client]:
    """Reconstruye el dominio sobre un servidor nuevo, sin reutilizar sockets.

    Returns:
        Jugadores históricos pendientes de recuperar sus sockets.

    Raises:
        ValueError: Si los datos no son compatibles o la sesión no es válida.

    """
    if (
        checkpoint.get("version") != CHECKPOINT_VERSION
        or checkpoint.get("theme") != server.theme
        or checkpoint.get("map_hash") != server.map_hash()
    ):
        msg = "Copia de recuperación incompatible con el mapa o la versión"
        raise ValueError(msg)
    server.detener()
    server.asynchronous = checkpoint.get("asynchronous", False)
    server.history.restore(
        checkpoint.get("history", {"version": 1, "initial": None, "records": []})
    )
    rules = ThemeRules(**{
        name: unpack(value) for name, value in checkpoint["rules"].items()
    })
    server._reglas = rules
    server.rules_profile = rules.theme
    server.mapa.configurar_reglas(rules)
    coordinator = server._game_coordinator
    coordinator._rules = rules
    restore(server, checkpoint["server"], _SERVER)
    server.estado._estado_actual = checkpoint["state"]
    restore(coordinator, checkpoint["config"], _CONFIG)
    server.situation_ruleset = coordinator.situation_ruleset()
    restore(server.objetivos_secretos, checkpoint["objectives"], _OBJECTIVES)
    sources = _restore_random_sources(checkpoint)
    server.objetivos_secretos._rng = sources["objectives"]
    coordinator._situation_rng = sources["situations"]
    if set(checkpoint["countries"]) != set(server.mapa.paises()):
        msg = "La copia no contiene todos los países"
        raise ValueError(msg)
    for name, values in checkpoint["countries"].items():
        country = server.mapa._mapa[name]
        country.unidades, country.jugador, country.misiles = values
    server.mapa._condominios = unpack(checkpoint["shared"])
    server.mazo.mazo = unpack(checkpoint["deck"])
    players = _restore_players(server, checkpoint["players"])
    _restore_game(server, checkpoint["game"], players, sources)
    server._command_executor = GameCommandExecutor(server)
    server._command_executor.start()
    return players


def _restore_players(
    server: Server, records: list[dict[str, Any]]
) -> dict[int, Client]:
    players: dict[int, Client] = {}
    for record in records:
        player = Client(
            record["userid"],
            cast("ConnectionServer", _OfflineConnection()),
            server,
            record["username"],
            soy_admin=record["userid"] == server._admin_user_id,
            reconnect_token=record["token"],
        )
        color = next(
            (
                color
                for color in server.color.colores()
                if color.to_hex() == record["color"]
            ),
            None,
        )
        player.asignar_color(color)
        if color is not None:
            server.color.reservar_color(color)
        player.import_command_cache(record["cache"])
        players[player.userid()] = player
    return players


def _restore_game(
    server: Server,
    data: dict[str, Any] | None,
    players: dict[int, Client],
    sources: dict[str, random.Random],
) -> None:
    coordinator = server._game_coordinator
    rules = server.reglas()
    if data is not None:
        deck = SituationDeck(rng=sources["deck"])
        restore(deck, data["situation_deck"], ("_cards", "_discard"))
        runtime = SituationRuntime(
            server.mapa, deck, dice_rng=sources["situation_dice"]
        )
        restore(runtime, data["situation"], _SITUATION)
        runtime._active_effect = create_effect(runtime._active_card)
        context = data["context"]
        runtime._context = SituationContext(
            server.mapa,
            context["round_number"],
            unpack(context["player_ids"]),
            unpack(context["player_colors"]),
        )
        game = Game(
            server.mapa,
            server.mazo,
            list(players.values()),
            server,
            coordinator._paises_para_victoria,
            objetivos_secretos_activados=coordinator._objetivos_secretos_activados,
            situation_runtime=runtime,
            rules=rules,
            dice_rng=sources["battle"],
        )
        restore(game, data["state"], _GAME)
        manager = game._turn_manager
        restore(manager, data["turn_manager"], _TURNS)
        manager._turn_factory = replace(
            manager._turn_factory, first_units=data["first_units"]
        )
        turns = []
        for turn_data in data["turns"]:
            kind = turn_data["type"]
            turn = manager._turn_factory.crear(0, _TURN_TYPES[kind])
            restore(turn, turn_data["state"], _TURN_FIELDS[kind])
            if isinstance(turn, SiguientesTurnos):
                for continent in CONTINENTS:
                    setattr(
                        turn,
                        f"_unidades_{continent.unit_suffix}",
                        turn._unidades_continentes.get(continent.map_id, 0),
                    )
            turns.append(turn)
        manager._turnos = turns
        restore(game._card_manager, data["cards"], _CARDS)
        restore(game.pactos(), data["pacts"], ("_pactos", "_next_id"))
        coordinator._game = game
