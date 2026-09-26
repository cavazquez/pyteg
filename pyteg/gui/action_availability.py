"""Disponibilidad de acciones visibles en la GUI.

La validación definitiva vive en el servidor. Esta proyección usa el estado
público y la selección local para no ofrecer acciones evidentemente inválidas
en el menú, la toolbar y las instrucciones de la barra de estado.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pyteg.config import MIN_UNITS_FOR_ATTACK, MIN_UNITS_TO_LEAVE, MISSILE_UNIT_COST
from pyteg.gui.gameplay_state import en_fase_reparto, es_mi_turno
from pyteg.gui.mapa.map_rules import (
    es_mi_pais,
    es_pais_enemigo,
    son_adyacentes,
    unidades_propias_en_pais,
)
from pyteg.gui.units_placement import unidades_colocables_en_pais
from pyteg.i18n import translate as _


class ReasonCode(StrEnum):
    """Motivos estables, traducidos sólo al mostrarlos."""

    DISCONNECTED = "disconnected"
    GAME_FINISHED = "game_finished"
    GAME_NOT_STARTED = "game_not_started"
    NOT_YOUR_TURN = "not_your_turn"
    PLACEMENT_PENDING = "placement_pending"
    ACTIONS_PHASE_ONLY = "actions_phase_only"
    PLACEMENT_PHASE_ONLY = "placement_phase_only"
    SELECT_TWO_COUNTRIES = "select_two_countries"
    SELECT_COUNTRY = "select_country"
    ORIGIN_NOT_OWNED = "origin_not_owned"
    COUNTRY_NOT_OWNED = "country_not_owned"
    ATTACK_ENEMY_ONLY = "attack_enemy_only"
    MOVE_OWN_ONLY = "move_own_only"
    MISSILE_ENEMY_ONLY = "missile_enemy_only"
    NOT_ADJACENT = "not_adjacent"
    INSUFFICIENT_ORIGIN_UNITS = "insufficient_origin_units"
    NO_REINFORCEMENTS = "no_reinforcements"
    NO_MISSILES = "no_missiles"
    MISSILES_DISABLED = "missiles_disabled"
    SHARED_MISSILE_TARGET = "shared_missile_target"
    INSUFFICIENT_MISSILE_UNITS = "insufficient_missile_units"
    ATTACK_NOT_YET_ALLOWED = "attack_not_yet_allowed"
    PLAYER_RESTING = "player_resting"
    OPEN_BORDERS = "open_borders"
    CLOSED_BORDERS = "closed_borders"
    COUNTRY_BLOCKED = "country_blocked"
    PACT_BLOCKED = "pact_blocked"


@dataclass(frozen=True, slots=True)
class ActionAvailability:
    """Estado de una acción y motivo de bloqueo independiente del idioma."""

    enabled: bool
    reason_code: ReasonCode | None = None
    reason_args: tuple[int, ...] = ()

    def explanation(self, enabled_help: str = "") -> str:
        """Devuelve la ayuda de la acción o el bloqueo en el idioma vigente.

        Returns:
            Explicación traducida que corresponde al estado de la acción.

        """
        if self.enabled or self.reason_code is None:
            return enabled_help
        messages = {
            ReasonCode.DISCONNECTED: _("Conectate al servidor"),
            ReasonCode.GAME_FINISHED: _("La partida terminó"),
            ReasonCode.GAME_NOT_STARTED: _("Esperá a que comience la partida"),
            ReasonCode.NOT_YOUR_TURN: _("Esperá tu turno"),
            ReasonCode.PLACEMENT_PENDING: _(
                "Colocá todas las unidades antes de continuar"
            ),
            ReasonCode.ACTIONS_PHASE_ONLY: _(
                "Esta acción requiere la fase de acciones"
            ),
            ReasonCode.PLACEMENT_PHASE_ONLY: _(
                "Esta acción requiere la fase de colocación"
            ),
            ReasonCode.SELECT_TWO_COUNTRIES: _("Seleccioná origen y destino"),
            ReasonCode.SELECT_COUNTRY: _("Seleccioná un país"),
            ReasonCode.ORIGIN_NOT_OWNED: _("El origen debe ser un país propio"),
            ReasonCode.COUNTRY_NOT_OWNED: _("Este país no te pertenece"),
            ReasonCode.ATTACK_ENEMY_ONLY: _("Sólo podés atacar un país enemigo"),
            ReasonCode.MOVE_OWN_ONLY: _("Sólo podés mover a un país propio"),
            ReasonCode.MISSILE_ENEMY_ONLY: _(
                "Sólo podés lanzar un misil a un país enemigo"
            ),
            ReasonCode.NOT_ADJACENT: _("Los países no son adyacentes"),
            ReasonCode.INSUFFICIENT_ORIGIN_UNITS: _(
                "El origen debe conservar al menos una unidad"
            ),
            ReasonCode.NO_REINFORCEMENTS: _("Sin unidades disponibles para este país"),
            ReasonCode.NO_MISSILES: _("El origen no tiene misiles"),
            ReasonCode.MISSILES_DISABLED: _("Los misiles están desactivados"),
            ReasonCode.SHARED_MISSILE_TARGET: _(
                "No se puede lanzar un misil a un país compartido"
            ),
            ReasonCode.INSUFFICIENT_MISSILE_UNITS: _(
                "Se necesitan al menos {} unidades para canjear un misil"
            ),
            ReasonCode.ATTACK_NOT_YET_ALLOWED: _(
                "Podés atacar a partir de la ronda {}"
            ),
            ReasonCode.PLAYER_RESTING: _(
                "Tu color está en descanso: no podés atacar ni mover"
            ),
            ReasonCode.OPEN_BORDERS: _(
                "Fronteras abiertas: sólo podés atacar entre continentes"
            ),
            ReasonCode.CLOSED_BORDERS: _(
                "Fronteras cerradas: sólo podés atacar dentro del continente"
            ),
            ReasonCode.COUNTRY_BLOCKED: _(
                "Este país está bloqueado para recibir refuerzos"
            ),
            ReasonCode.PACT_BLOCKED: _("Un pacto público impide atacar ese objetivo"),
        }
        return messages[self.reason_code].format(*self.reason_args)


@dataclass(frozen=True, slots=True)
class SelectionAvailability:
    """Acciones que dependen del turno y del par origen/destino."""

    attack: ActionAvailability
    move: ActionAvailability
    launch_missile: ActionAvailability
    finish_turn: ActionAvailability
    cards: ActionAvailability


@dataclass(frozen=True, slots=True)
class CountryAvailability:
    """Acciones que dependen del país bajo el cursor."""

    place: ActionAvailability
    exchange_missile: ActionAvailability
    missile_unit_cost: int
    placeable_units: int


@dataclass(frozen=True, slots=True)
class _PactAction:
    """Datos del par y la ronda que usa la proyección de pactos."""

    attacker: int
    origin: str
    destination: str
    origin_continent: str | None
    destination_continent: str | None
    round_number: int


_ALLOWED = ActionAvailability(enabled=True)
_PACT_PLAYER_COUNT = 2
_DUEL_PLAYER_COUNT = 2


def _blocked(reason: ReasonCode, *args: int) -> ActionAvailability:
    return ActionAvailability(enabled=False, reason_code=reason, reason_args=args)


def _snapshot(main_window: Any) -> dict[str, Any]:
    model = getattr(main_window, "client_state_model", None)
    snapshot = getattr(model, "snapshot", None)
    return snapshot if isinstance(snapshot, dict) else {}


def _rules(main_window: Any) -> dict[str, Any]:
    model = getattr(main_window, "client_state_model", None)
    rules = getattr(model, "rules", None)
    if isinstance(rules, dict):
        return rules
    rules = _snapshot(main_window).get("reglas")
    return rules if isinstance(rules, dict) else {}


def _rule_int(main_window: Any, key: str, default: int) -> int:
    value = _rules(main_window).get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _connected(main_window: Any) -> bool:
    transmitter = getattr(main_window, "transmisor", None)
    check = getattr(transmitter, "esta_conectado", None)
    return bool(check()) if callable(check) else False


def _common_reason(main_window: Any) -> ReasonCode | None:
    if not _connected(main_window):
        return ReasonCode.DISCONNECTED
    if getattr(main_window, "partida_finalizada", False) is True:
        return ReasonCode.GAME_FINISHED
    state = getattr(main_window, "estado_actual", None)
    if isinstance(state, str) and state != "JUGANDO":
        return ReasonCode.GAME_NOT_STARTED
    if not es_mi_turno(main_window):
        return ReasonCode.NOT_YOUR_TURN
    return None


def _phase_reason(main_window: Any, expected: str) -> ReasonCode | None:
    phase = getattr(main_window, "fase_actual", None)
    if isinstance(phase, str):
        if phase == expected:
            return None
        if phase == "colocacion":
            return ReasonCode.PLACEMENT_PENDING
        return (
            ReasonCode.ACTIONS_PHASE_ONLY
            if expected == "acciones"
            else ReasonCode.PLACEMENT_PHASE_ONLY
        )
    if en_fase_reparto(main_window):
        return None if expected == "colocacion" else ReasonCode.PLACEMENT_PENDING
    return None if expected == "acciones" else ReasonCode.PLACEMENT_PHASE_ONLY


def _country_widget(main_window: Any, country: str | None) -> Any | None:
    scene = getattr(main_window, "scene", None)
    countries = getattr(scene, "paises", None)
    if not isinstance(countries, dict) or not country:
        return None
    return countries.get(country)


def _is_shared_country(main_window: Any, country: str) -> bool:
    countries = _snapshot(main_window).get("countries")
    data = countries.get(country) if isinstance(countries, dict) else None
    return isinstance(data, dict) and data.get("compartido") is True


def _country_int(
    main_window: Any, country: str, method_name: str, field: str
) -> int | None:
    widget = _country_widget(main_window, country)
    method = getattr(widget, method_name, None)
    value = method() if callable(method) else None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    countries = _snapshot(main_window).get("countries")
    data = countries.get(country) if isinstance(countries, dict) else None
    value = data.get(field) if isinstance(data, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _attack_round_reason(main_window: Any) -> ActionAvailability | None:
    snapshot = _snapshot(main_window)
    turn = snapshot.get("turno")
    round_number = turn.get("num_ronda") if isinstance(turn, dict) else None
    if not isinstance(round_number, int):
        return None
    first_rounds = _rule_int(main_window, "first_turns_no_attack", 0)
    rules = _rules(main_window)
    players = snapshot.get("players")
    if (
        rules.get("theme") == "revancha"
        and isinstance(players, list)
        and len(players) == _DUEL_PLAYER_COUNT
    ):
        first_rounds = 1
    if first_rounds > 0 and round_number <= first_rounds:
        return _blocked(ReasonCode.ATTACK_NOT_YET_ALLOWED, first_rounds + 1)
    return None


def _situation(main_window: Any) -> dict[str, Any]:
    situation = _snapshot(main_window).get("situacion")
    return situation if isinstance(situation, dict) else {}


def _resting(main_window: Any) -> bool:
    situation = _situation(main_window)
    if situation.get("efecto") != "rest":
        return False
    color_key = situation.get("parametro")
    if not isinstance(color_key, str):
        return False
    client = getattr(main_window, "client", None)
    userid = client.userid() if client is not None else None
    colors = getattr(main_window, "colores", None)
    assigned = colors.color_asignado(userid) if colors is not None and userid else None
    name = getattr(assigned, "name", None)
    return callable(name) and name().lower() == color_key.lower()


def _continent(main_window: Any, country: str) -> str | None:
    widget = _country_widget(main_window, country)
    getter = getattr(widget, "continente", None)
    value = getter() if callable(getter) else None
    return value if isinstance(value, str) else None


def _border_reason(
    main_window: Any, origin: str, destination: str
) -> ReasonCode | None:
    effect = _situation(main_window).get("efecto")
    if effect not in {"open_borders", "closed_borders"}:
        return None
    origin_continent = _continent(main_window, origin)
    destination_continent = _continent(main_window, destination)
    if origin_continent is None or destination_continent is None:
        return None
    if effect == "open_borders" and origin_continent == destination_continent:
        return ReasonCode.OPEN_BORDERS
    if effect == "closed_borders" and origin_continent != destination_continent:
        return ReasonCode.CLOSED_BORDERS
    return None


def _blocked_for_reinforcement(main_window: Any, country: str) -> bool:
    blocks = _snapshot(main_window).get("bloqueos")
    if not isinstance(blocks, list):
        return False
    client = getattr(main_window, "client", None)
    userid = client.userid() if client is not None else None
    return any(
        isinstance(block, dict)
        and block.get("pais") == country
        and block.get("jugador") == userid
        for block in blocks
    )


def _pact_defenders(
    main_window: Any, destination: str, attacker: int, *, missile: bool
) -> list[int]:
    """Obtiene los posibles defensores; en condominio el ataque elige uno.

    Returns:
        ID de los ocupantes elegibles, o lista vacía si faltan datos.

    """
    countries = _snapshot(main_window).get("countries")
    country = countries.get(destination) if isinstance(countries, dict) else None
    if not isinstance(country, dict):
        return []
    owner = country.get("userid")
    if missile or country.get("compartido") is not True:
        return [owner] if isinstance(owner, int) else []

    occupants = country.get("ocupantes")
    if not isinstance(occupants, list):
        return []
    return [
        occupant["userid"]
        for occupant in occupants
        if isinstance(occupant, dict)
        and isinstance(occupant.get("userid"), int)
        and occupant["userid"] != attacker
        and isinstance(occupant.get("unidades"), int)
        and occupant["unidades"] > 0
    ]


def _pact_forbids_defender(
    pacts: list[Any], action: _PactAction, defender: int
) -> bool:
    """Proyecta la regla pública de PactManager.puede_atacar.

    Returns:
        True si un pacto vigente bloquea este defensor.

    """
    for pact in pacts:
        if not isinstance(pact, dict):
            continue
        if pact.get("estado") not in {"activo", "ruptura_anunciada"}:
            continue
        until = pact.get("ronda_hasta")
        if isinstance(until, int) and action.round_number > until:
            continue
        players = pact.get("jugadores")
        if (
            not isinstance(players, list)
            or len(players) != _PACT_PLAYER_COUNT
            or not all(isinstance(player, int) for player in players)
            or {action.attacker, defender} != set(players)
        ):
            continue
        if pact.get("tipo") == "agresion":
            return True
        countries = pact.get("paises")
        continents = pact.get("continentes")
        target = pact.get("pais_objetivo")
        country_restricted = isinstance(countries, list) and (
            action.origin in countries or action.destination in countries
        )
        continent_restricted = isinstance(continents, list) and (
            action.origin_continent in continents
            or action.destination_continent in continents
        )
        if (
            country_restricted
            or continent_restricted
            or target in {action.origin, action.destination}
        ):
            return True
    return False


def _pact_context(
    main_window: Any, origin: str, destination: str
) -> tuple[list[Any], _PactAction] | None:
    """Reúne los datos públicos necesarios para consultar pactos.

    Returns:
        Pactos y datos del ataque, o None cuando faltan datos públicos.

    """
    snapshot = _snapshot(main_window)
    pacts = snapshot.get("pactos")
    turn = snapshot.get("turno")
    round_number = turn.get("num_ronda") if isinstance(turn, dict) else None
    client = getattr(main_window, "client", None)
    userid = client.userid() if client is not None else None
    if not isinstance(pacts, list) or not isinstance(round_number, int) or not userid:
        return None
    attacker = int(userid)
    action = _PactAction(
        attacker,
        origin,
        destination,
        _continent(main_window, origin),
        _continent(main_window, destination),
        round_number,
    )
    return pacts, action


def pact_allows_defender(
    main_window: Any, origin: str, destination: str, defender: int
) -> bool:
    """Consulta si un pacto público permite atacar a un ocupante concreto.

    Returns:
        True si no hay bloqueo público; el servidor conserva la validación final.

    """
    context = _pact_context(main_window, origin, destination)
    if context is None:
        return True
    pacts, action = context
    return not _pact_forbids_defender(pacts, action, defender)


def _pact_blocks_action(
    main_window: Any, origin: str, destination: str, *, missile: bool = False
) -> bool:
    """Bloquea sólo si el pacto prohíbe todos los objetivos elegibles.

    Returns:
        True si ningún defensor elegible admite la acción.

    """
    context = _pact_context(main_window, origin, destination)
    if context is None:
        return False
    pacts, action = context
    defenders = _pact_defenders(
        main_window, destination, action.attacker, missile=missile
    )
    if not defenders:
        return False
    return all(
        _pact_forbids_defender(pacts, action, defender) for defender in defenders
    )


def _selected_pair(
    main_window: Any, origin: str | None, destination: str | None
) -> tuple[str | None, str | None]:
    """Resuelve parámetros explícitos contra la selección visible.

    Returns:
        País de origen y destino, si se conocen.

    """
    if origin and destination:
        return origin, destination
    scene = getattr(main_window, "scene", None)
    selection = getattr(scene, "selection_manager", None)
    if selection is None:
        return origin, destination
    return (
        origin or selection.get_pais_origen(),
        destination or selection.get_pais_destino(),
    )


def _origin_has_units(main_window: Any, origin: str) -> bool:
    """Comprueba si el jugador puede dejar una guarnición en el origen.

    Returns:
        True si hay suficientes unidades o aún no llegó el dato público.

    """
    units = unidades_propias_en_pais(main_window, origin)
    if units is None:
        units = _country_int(main_window, origin, "get_unidades", "unidades")
    return units is None or units >= MIN_UNITS_FOR_ATTACK


def _attack_availability(
    main_window: Any,
    origin: str,
    destination: str,
    *,
    adjacent: bool,
    has_units: bool,
) -> ActionAvailability:
    """Evalúa ataque incluyendo restricciones públicas de Revancha.

    Returns:
        Disponibilidad del ataque para el par.

    """
    reason: ReasonCode | None
    if not es_pais_enemigo(main_window, destination):
        reason = ReasonCode.ATTACK_ENEMY_ONLY
    elif not adjacent:
        reason = ReasonCode.NOT_ADJACENT
    elif not has_units:
        reason = ReasonCode.INSUFFICIENT_ORIGIN_UNITS
    elif _resting(main_window):
        reason = ReasonCode.PLAYER_RESTING
    else:
        reason = _border_reason(main_window, origin, destination)
    if reason is not None:
        return _blocked(reason)
    if round_reason := _attack_round_reason(main_window):
        return round_reason
    if _pact_blocks_action(main_window, origin, destination):
        return _blocked(ReasonCode.PACT_BLOCKED)
    return _ALLOWED


def _move_availability(
    main_window: Any, destination: str, *, adjacent: bool, has_units: bool
) -> ActionAvailability:
    """Evalúa movimiento entre países ocupados por el jugador.

    Returns:
        Disponibilidad del movimiento para el par.

    """
    if not es_mi_pais(main_window, destination):
        return _blocked(ReasonCode.MOVE_OWN_ONLY)
    if not adjacent:
        return _blocked(ReasonCode.NOT_ADJACENT)
    if not has_units:
        return _blocked(ReasonCode.INSUFFICIENT_ORIGIN_UNITS)
    if _resting(main_window):
        return _blocked(ReasonCode.PLAYER_RESTING)
    return _ALLOWED


def _missile_availability(
    main_window: Any, origin: str, destination: str
) -> ActionAvailability:
    """Evalúa lanzamiento de misil según el estado público.

    Returns:
        Disponibilidad del lanzamiento para el par.

    """
    if not getattr(main_window, "misiles_habilitados", False):
        return _blocked(ReasonCode.MISSILES_DISABLED)
    if es_mi_pais(main_window, destination) or not es_pais_enemigo(
        main_window, destination
    ):
        return _blocked(ReasonCode.MISSILE_ENEMY_ONLY)
    if _is_shared_country(main_window, destination):
        return _blocked(ReasonCode.SHARED_MISSILE_TARGET)
    missiles = _country_int(main_window, origin, "get_cantidad_misiles", "misiles")
    if missiles is None or missiles < 1:
        return _blocked(ReasonCode.NO_MISSILES)
    if _pact_blocks_action(main_window, origin, destination, missile=True):
        return _blocked(ReasonCode.PACT_BLOCKED)
    return _ALLOWED


def selection_availability(
    main_window: Any,
    origin: str | None = None,
    destination: str | None = None,
) -> SelectionAvailability:
    """Calcula disponibilidad del par usando un mismo criterio para toda la GUI.

    Returns:
        Estado de atacar, mover, misil, finalizar turno y tarjetas.

    """
    origin, destination = _selected_pair(main_window, origin, destination)
    common = _common_reason(main_window)
    cards = _ALLOWED if _connected(main_window) else _blocked(ReasonCode.DISCONNECTED)
    if common is not None:
        unavailable = _blocked(common)
        return SelectionAvailability(
            unavailable, unavailable, unavailable, unavailable, cards
        )

    phase = _phase_reason(main_window, "acciones")
    if phase is not None:
        unavailable = _blocked(phase)
        return SelectionAvailability(
            unavailable, unavailable, unavailable, unavailable, cards
        )

    finish = _ALLOWED
    if not origin or not destination:
        missing = _blocked(ReasonCode.SELECT_TWO_COUNTRIES)
        return SelectionAvailability(missing, missing, missing, finish, cards)

    if not es_mi_pais(main_window, origin):
        invalid = _blocked(ReasonCode.ORIGIN_NOT_OWNED)
        return SelectionAvailability(invalid, invalid, invalid, finish, cards)

    has_units = _origin_has_units(main_window, origin)
    theme = getattr(main_window, "map_theme", "classic")
    if not isinstance(theme, str):
        theme = "classic"
    adjacent = son_adyacentes(theme, origin, destination)

    return SelectionAvailability(
        _attack_availability(
            main_window, origin, destination, adjacent=adjacent, has_units=has_units
        ),
        _move_availability(
            main_window, destination, adjacent=adjacent, has_units=has_units
        ),
        _missile_availability(main_window, origin, destination),
        finish,
        cards,
    )


def country_availability(
    main_window: Any, country: str | None, continent: str | None
) -> CountryAvailability:
    """Calcula colocación y canje en el país del menú contextual.

    Returns:
        Estado de las acciones propias del país y límites visibles.

    """
    cost = _rule_int(main_window, "missile_unit_cost", MISSILE_UNIT_COST)
    leave = _rule_int(main_window, "missile_min_units_to_leave", MIN_UNITS_TO_LEAVE)
    if country and _is_shared_country(main_window, country):
        leave = max(1, leave)
    last_units = getattr(main_window, "last_units", {})
    placeable = (
        unidades_colocables_en_pais(last_units, continent)[0]
        if isinstance(last_units, dict) and continent is not None
        else 0
    )
    common = _common_reason(main_window)
    if common is not None:
        blocked = _blocked(common)
        return CountryAvailability(blocked, blocked, cost, placeable)
    if not country:
        blocked = _blocked(ReasonCode.SELECT_COUNTRY)
        return CountryAvailability(blocked, blocked, cost, placeable)
    if not es_mi_pais(main_window, country):
        blocked = _blocked(ReasonCode.COUNTRY_NOT_OWNED)
        return CountryAvailability(blocked, blocked, cost, placeable)

    place = _place_availability(main_window, country, placeable)
    exchange = _exchange_availability(main_window, country, cost, leave)
    return CountryAvailability(place, exchange, cost, placeable)


def _place_availability(
    main_window: Any, country: str, placeable: int
) -> ActionAvailability:
    """Evalúa los refuerzos de un país propio.

    Returns:
        Estado de la acción de colocar.

    """
    place_phase = _phase_reason(main_window, "colocacion")
    if place_phase is not None:
        return _blocked(place_phase)
    if placeable < 1:
        return _blocked(ReasonCode.NO_REINFORCEMENTS)
    if _blocked_for_reinforcement(main_window, country):
        return _blocked(ReasonCode.COUNTRY_BLOCKED)
    return _ALLOWED


def _exchange_availability(
    main_window: Any, country: str, cost: int, leave: int
) -> ActionAvailability:
    """Evalúa el canje de unidades propias por un misil.

    Returns:
        Estado de la acción de canje.

    """
    exchange_phase = _phase_reason(main_window, "acciones")
    if not getattr(main_window, "misiles_habilitados", False):
        return _blocked(ReasonCode.MISSILES_DISABLED)
    if exchange_phase is not None:
        return _blocked(exchange_phase)
    units = unidades_propias_en_pais(main_window, country)
    if units is None:
        units = _country_int(main_window, country, "get_unidades", "unidades")
    if units is not None and units < cost + leave:
        return _blocked(ReasonCode.INSUFFICIENT_MISSILE_UNITS, cost + leave)
    return _ALLOWED
