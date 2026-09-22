"""Validación en runtime del contrato JSON que viaja por TCP."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

type FieldValidator = Callable[[object], bool]

_ERROR_INVALID_PAYLOAD = "invalid_payload"
_ERROR_INVALID_MESSAGE = "invalid_message"
_ERROR_UNKNOWN_MESSAGE = "unknown_message"
_ERROR_INVALID_FIELD = "invalid_field"
_ERROR_MISSING_FIELD = "missing_field"
_CARDS_PER_EXCHANGE = 3


class MessageValidationError(ValueError):
    """Un mensaje JSON no cumple el contrato de red."""

    def __init__(self, code: str, message: str) -> None:
        """Inicializa el error con un código estable y texto diagnóstico.

        Args:
            code: Código apto para enviar como ``error_type`` al peer.
            message: Explicación legible del campo o mensaje rechazado.

        """
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class _MessageSchema:
    """Reglas de campos obligatorios y opcionales de un mensaje conocido."""

    required: Mapping[str, FieldValidator]
    optional: Mapping[str, FieldValidator]
    allow_unknown: bool = False


def _is_string(value: object) -> bool:
    return isinstance(value, str)


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_boolean(value: object) -> bool:
    return type(value) is bool


def _integer_in_range(minimum: int, maximum: int | None = None) -> FieldValidator:
    """Crea un validador de enteros que no acepta booleanos.

    Args:
        minimum: Valor mínimo permitido, inclusive.
        maximum: Valor máximo permitido, inclusive si se indica.

    Returns:
        Predicado para el rango configurado.

    """

    def validate(value: object) -> bool:
        if type(value) is not int or value < minimum:
            return False
        return maximum is None or value <= maximum

    return validate


def _nullable(validator: FieldValidator) -> FieldValidator:
    def validate(value: object) -> bool:
        return value is None or validator(value)

    return validate


def _is_rgb(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {"r", "g", "b"}:
        return False
    component = _integer_in_range(0, 255)
    return all(component(value[name]) for name in ("r", "g", "b"))


def _is_units(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    count = _integer_in_range(0)
    return all(
        isinstance(kind, str) and count(amount) for kind, amount in value.items()
    )


def _is_card(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    allowed = {"pais", "simbolo", "index"}
    if not {"pais", "simbolo"}.issubset(value) or not set(value).issubset(allowed):
        return False
    if not _is_nonempty_string(value["pais"]) or not _is_nonempty_string(
        value["simbolo"]
    ):
        return False
    return "index" not in value or _integer_in_range(0)(value["index"])


def _is_card_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == _CARDS_PER_EXCHANGE
        and all(_is_card(card) for card in value)
    )


def _is_card_collection(value: object) -> bool:
    return isinstance(value, list) and all(_is_card(card) for card in value)


def _is_player_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    user_id = _integer_in_range(1)
    for player in value:
        if not isinstance(player, dict) or set(player) != {"userid", "color"}:
            return False
        if not user_id(player["userid"]) or not _is_rgb(player["color"]):
            return False
    return True


def _is_battle_result(value: object) -> bool:
    allowed = {"atacante", "defensor", "restar"}
    if not isinstance(value, dict) or "restar" not in value:
        return False
    if not set(value).issubset(allowed):
        return False
    losses = value["restar"]
    if not isinstance(losses, list) or not all(
        isinstance(name, str) for name in losses
    ):
        return False
    return all(
        isinstance(value.get(name), str) and bool(value[name])
        for name in ("atacante", "defensor")
        if name in value
    )


def _is_integer_list(value: object) -> bool:
    return isinstance(value, list) and all(type(item) is int for item in value)


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(_is_nonempty_string(item) for item in value)


def _is_snapshot_players(value: object) -> bool:  # noqa: PLR0911
    if not isinstance(value, list):
        return False
    required = {
        "userid",
        "username",
        "color",
        "admin",
        "connected",
        "eliminated",
    }
    for player in value:
        if not isinstance(player, dict):
            return False
        if not required.issubset(player):
            return False
        if not _integer_in_range(1)(player["userid"]):
            return False
        if not _is_string(player["username"]):
            return False
        if not _nullable(_is_rgb)(player["color"]):
            return False
        if (
            not _is_boolean(player["admin"])
            or not _is_boolean(player["connected"])
            or not _is_boolean(player["eliminated"])
        ):
            return False
    return True


def _is_snapshot_countries(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    for name, country in value.items():
        if not _is_nonempty_string(name) or not isinstance(country, dict):
            return False
        if not {"userid", "unidades", "misiles"}.issubset(country):
            return False
        if not _nullable(_integer_in_range(1))(country["userid"]):
            return False
        if not _integer_in_range(0)(country["unidades"]) or not _integer_in_range(0)(
            country["misiles"]
        ):
            return False
    return True


def _is_snapshot_turn(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        {"num_turno", "num_ronda", "jugador_id"}.issubset(value)
        and _integer_in_range(0)(value["num_turno"])
        and _integer_in_range(1)(value["num_ronda"])
        and _nullable(_integer_in_range(1))(value["jugador_id"])
    )


def _is_snapshot_configuration(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "segundos_por_turno",
        "paises_para_victoria",
        "objetivos_secretos",
        "misiles_habilitados",
    }
    return (
        required.issubset(value)
        and _integer_in_range(1)(value["segundos_por_turno"])
        and _integer_in_range(0)(value["paises_para_victoria"])
        and _is_boolean(value["objetivos_secretos"])
        and _is_boolean(value["misiles_habilitados"])
    )


_POSITIVE_INTEGER = _integer_in_range(1)
_NONNEGATIVE_INTEGER = _integer_in_range(0)
_DICE_COUNT = _integer_in_range(1, 3)

_SERVER_COMMAND_SCHEMAS: dict[str, _MessageSchema] = {
    "solicitar_snapshot": _MessageSchema({}, {}),
    "hello": _MessageSchema(
        {
            "protocol_version": _is_nonempty_string,
            "theme": _is_nonempty_string,
            "map_hash": _is_nonempty_string,
        },
        {"capabilities": _is_string_list, "rules": _is_string_list},
    ),
    "pong": _MessageSchema({"heartbeat_id": _is_nonempty_string}, {}),
    "chat": _MessageSchema({"msg": _is_string}, {}),
    "empezar": _MessageSchema(
        {},
        {
            "segundos": _POSITIVE_INTEGER,
            "paises_para_victoria": _NONNEGATIVE_INTEGER,
            "objetivos_secretos": _is_boolean,
            "misiles_habilitados": _is_boolean,
        },
    ),
    "empezar_partida": _MessageSchema({}, {}),
    "volver_lobby": _MessageSchema({}, {}),
    "seleccionar_color": _MessageSchema({"color": _is_nonempty_string}, {}),
    "set_username": _MessageSchema({"username": _is_nonempty_string}, {}),
    "reconectar": _MessageSchema(
        {"user_id": _POSITIVE_INTEGER, "token": _is_nonempty_string}, {}
    ),
    "agregar_unidad": _MessageSchema(
        {
            "pais": _is_nonempty_string,
            "tipo_unidad": _is_nonempty_string,
            "cantidad": _POSITIVE_INTEGER,
        },
        {},
    ),
    "mover_unidad": _MessageSchema(
        {
            "origen": _is_nonempty_string,
            "destino": _is_nonempty_string,
            "cantidad": _POSITIVE_INTEGER,
        },
        {},
    ),
    "atacar": _MessageSchema(
        {
            "origen": _is_nonempty_string,
            "destino": _is_nonempty_string,
        },
        {"cantidad_unidades": _DICE_COUNT},
    ),
    "finalizar_turno": _MessageSchema({}, {}),
    "solicitar_tarjetas": _MessageSchema({}, {}),
    "reclamar_tarjeta": _MessageSchema({}, {}),
    "canje_especial": _MessageSchema({"pais": _is_nonempty_string}, {}),
    "canjear_tarjetas": _MessageSchema({"tarjetas": _is_card_list}, {}),
    "canjear_misil": _MessageSchema({"pais": _is_nonempty_string}, {}),
    "lanzar_misil": _MessageSchema(
        {"pais_origen": _is_nonempty_string, "pais_destino": _is_nonempty_string},
        {},
    ),
}

_CLIENT_EVENT_SCHEMAS: dict[str, _MessageSchema] = {
    "snapshot": _MessageSchema(
        {
            "snapshot_version": _POSITIVE_INTEGER,
            "revision": _NONNEGATIVE_INTEGER,
            "estado": _is_nonempty_string,
            "theme": _is_nonempty_string,
            "map_hash": _is_nonempty_string,
            "configuracion": _is_snapshot_configuration,
            "players": _is_snapshot_players,
            "countries": _is_snapshot_countries,
            "fase": _nullable(_is_nonempty_string),
            "turno": _nullable(_is_snapshot_turn),
            "refuerzos_pendientes": _NONNEGATIVE_INTEGER,
        },
        {"resync": _is_boolean},
        allow_unknown=True,
    ),
    "command_result": _MessageSchema(
        {
            "command_id": _is_nonempty_string,
            "accepted": _is_boolean,
            "revision": _NONNEGATIVE_INTEGER,
        },
        {"error_code": _is_nonempty_string},
    ),
    "hello": _MessageSchema(
        {
            "protocol_version": _is_nonempty_string,
            "theme": _is_nonempty_string,
            "map_hash": _is_nonempty_string,
        },
        {"capabilities": _is_string_list, "rules": _is_string_list},
    ),
    "hello_ack": _MessageSchema({"accepted": _is_boolean}, {}),
    "ping": _MessageSchema({"heartbeat_id": _is_nonempty_string}, {}),
    "chat": _MessageSchema({"msg": _is_string}, {"msg_type": _is_string}),
    "sosadmin": _MessageSchema({}, {}),
    "estado": _MessageSchema({"estado": _is_nonempty_string}, {}),
    "fase": _MessageSchema(
        {"fase": _is_nonempty_string, "jugador_id": _POSITIVE_INTEGER},
        {"unidades_pendientes": _NONNEGATIVE_INTEGER},
    ),
    "color_asignado": _MessageSchema(
        {
            "id": _POSITIVE_INTEGER,
            "r": _integer_in_range(0, 255),
            "g": _integer_in_range(0, 255),
            "b": _integer_in_range(0, 255),
        },
        {},
    ),
    "color": _MessageSchema(
        {
            "r": _integer_in_range(0, 255),
            "g": _integer_in_range(0, 255),
            "b": _integer_in_range(0, 255),
        },
        {},
    ),
    "user_id": _MessageSchema({"user_id": _POSITIVE_INTEGER}, {}),
    "session_token": _MessageSchema(
        {"user_id": _POSITIVE_INTEGER, "token": _is_nonempty_string}, {}
    ),
    "reconexion": _MessageSchema(
        {
            "user_id": _POSITIVE_INTEGER,
            "temporary_user_id": _POSITIVE_INTEGER,
        },
        {},
    ),
    "username": _MessageSchema(
        {"username": _is_string, "user_id": _POSITIVE_INTEGER}, {}
    ),
    "turno": _MessageSchema(
        {"num_turno": _NONNEGATIVE_INTEGER, "num_ronda": _POSITIVE_INTEGER},
        {
            "jugador_actual_id": _POSITIVE_INTEGER,
            "jugador_actual_nombre": _is_string,
            "jugador_actual_color": _is_string,
        },
    ),
    "tiempo": _MessageSchema(
        {"tiempo": _NONNEGATIVE_INTEGER}, {"user_id": _POSITIVE_INTEGER}
    ),
    "pais": _MessageSchema(
        {
            "pais": _is_nonempty_string,
            "userid": _nullable(_POSITIVE_INTEGER),
            "unidades": _NONNEGATIVE_INTEGER,
        },
        {},
    ),
    "unidades_disponibles": _MessageSchema({"unidades": _is_units}, {}),
    "actualizar_lista_jugadores": _MessageSchema({"jugadores": _is_player_list}, {}),
    "error": _MessageSchema(
        {"error_type": _is_nonempty_string, "message": _is_string}, {}
    ),
    "resultado_batalla": _MessageSchema(
        {
            "origen": _is_nonempty_string,
            "destino": _is_nonempty_string,
            "atacante_id": _nullable(_POSITIVE_INTEGER),
            "defensor_id": _nullable(_POSITIVE_INTEGER),
            "atacante": _is_string,
            "defensor": _is_string,
            "dados_atacante": _is_integer_list,
            "dados_defensor": _is_integer_list,
            "resultado": _is_battle_result,
            "conquistado": _is_boolean,
        },
        {},
    ),
    "victoria": _MessageSchema(
        {"ganador_id": _POSITIVE_INTEGER, "ganador_nombre": _is_nonempty_string},
        {},
    ),
    "configuracion_partida": _MessageSchema(
        {
            "segundos_por_turno": _POSITIVE_INTEGER,
            "paises_para_victoria": _NONNEGATIVE_INTEGER,
            "objetivos_secretos": _is_boolean,
            "misiles_habilitados": _is_boolean,
        },
        {},
    ),
    "tarjetas_jugador": _MessageSchema(
        {"tarjetas": _is_card_collection},
        {},
    ),
    "canje_especial": _MessageSchema(
        {
            "pais": _is_nonempty_string,
            "unidades_agregadas": _POSITIVE_INTEGER,
        },
        {},
    ),
    "objetivo_secreto": _MessageSchema(
        {"objetivo_id": _is_nonempty_string, "descripcion": _is_string}, {}
    ),
    "resultado_misil": _MessageSchema(
        {
            "jugador_id": _nullable(_POSITIVE_INTEGER),
            "jugador": _is_string,
            "pais_origen": _is_nonempty_string,
            "pais_destino": _is_nonempty_string,
            "distancia": _NONNEGATIVE_INTEGER,
            "dano": _NONNEGATIVE_INTEGER,
            "unidades_restantes": _NONNEGATIVE_INTEGER,
        },
        {},
    ),
    "misil_agregado": _MessageSchema(
        {"pais": _is_nonempty_string, "cantidad_misiles": _NONNEGATIVE_INTEGER},
        {},
    ),
}


def _validate_message(  # noqa: C901
    payload: object,
    schemas: Mapping[str, _MessageSchema],
    *,
    kind: str,
) -> dict[str, Any]:
    """Valida un objeto contra el conjunto de esquemas de una dirección TCP.

    Args:
        payload: Valor producido por ``json.loads``.
        schemas: Contratos permitidos para el peer receptor.
        kind: Nombre para describir el mensaje en errores.

    Returns:
        El payload validado como diccionario JSON.

    Raises:
        MessageValidationError: Si el payload no cumple el contrato.

    """
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) for key in payload
    ):
        msg = f"El {kind} debe ser un objeto JSON"
        raise MessageValidationError(_ERROR_INVALID_PAYLOAD, msg)

    discriminator = payload.get("mensaje")
    if not isinstance(discriminator, str):
        msg = f"El {kind} debe incluir el discriminador textual 'mensaje'"
        raise MessageValidationError(_ERROR_INVALID_MESSAGE, msg)

    schema = schemas.get(discriminator)
    if schema is None:
        msg = f"Mensaje desconocido: {discriminator}"
        raise MessageValidationError(_ERROR_UNKNOWN_MESSAGE, msg)

    # Todos los comandos pueden llevar un identificador de idempotencia. Aquí
    # sólo se valida su forma; el executor exige su presencia en mutaciones y
    # deja opcionales las consultas y demás mensajes no mutantes.
    allowed_fields = {"mensaje", "command_id", *schema.required, *schema.optional}
    unexpected = sorted(set(payload).difference(allowed_fields))
    if unexpected and not schema.allow_unknown:
        msg = f"Campo(s) no permitido(s) en {discriminator}: {', '.join(unexpected)}"
        raise MessageValidationError(_ERROR_INVALID_FIELD, msg)

    if "command_id" in payload and not _is_nonempty_string(payload["command_id"]):
        msg = f"El campo 'command_id' no es válido para {discriminator}"
        raise MessageValidationError(_ERROR_INVALID_FIELD, msg)

    for field, validator in schema.required.items():
        if field not in payload:
            msg = f"Falta el campo obligatorio '{field}' en {discriminator}"
            raise MessageValidationError(_ERROR_MISSING_FIELD, msg)
        if not validator(payload[field]):
            msg = f"El campo '{field}' no es válido para {discriminator}"
            raise MessageValidationError(_ERROR_INVALID_FIELD, msg)

    for field, validator in schema.optional.items():
        if field in payload and not validator(payload[field]):
            msg = f"El campo '{field}' no es válido para {discriminator}"
            raise MessageValidationError(_ERROR_INVALID_FIELD, msg)

    return cast("dict[str, Any]", payload)


def validate_server_command(payload: object) -> dict[str, Any]:
    """Valida un comando recibido por el servidor desde un cliente.

    Args:
        payload: Valor JSON recibido desde la conexión TCP.

    Returns:
        Comando validado listo para construir una tarea de servidor.

    """
    return _validate_message(payload, _SERVER_COMMAND_SCHEMAS, kind="comando")


def validate_client_event(payload: object) -> dict[str, Any]:
    """Valida un evento recibido por el cliente desde el servidor.

    Args:
        payload: Valor JSON recibido desde la conexión TCP.

    Returns:
        Evento validado listo para construir una tarea de cliente.

    """
    return _validate_message(payload, _CLIENT_EVENT_SCHEMAS, kind="evento")
