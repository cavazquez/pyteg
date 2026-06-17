"""Sincronización de estado de partida con los clientes conectados.

Centraliza el envío de turno, unidades, colores y lista de jugadores para
evitar duplicación entre `Server` y `ServerGameCoordinator`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pyteg.logger import get_logger
from pyteg.server.conexion.cliente import Client

if TYPE_CHECKING:
    from pyteg.server.conexion.broadcaster import ServerMessageBroadcaster
    from pyteg.server.juego.game import Game
    from pyteg.server.juego.mapa import Mapa

LOGGER = get_logger(__name__)

GetClients = Callable[[], list[Client]]
GetClientById = Callable[[int], Client | None]


def clientes_por_id(clients: list[Client]) -> dict[int, Client]:
    """Mapeo userid -> Client.

    Returns:
        Diccionario con clave `userid` (int) y valor `Client`.

    """
    return {int(c.userid()): c for c in clients}


def clientes_ordenados_por_turno(
    game: Game | None, clients: list[Client]
) -> list[Client]:
    """Clientes en orden de turno, con el resto al final.

    Returns:
        Lista de clientes ordenada según el turno actual del juego.

    """
    if game is None:
        return clients

    jugadores_orden_ids = game.lista_jugadores_orden_turno()
    por_id = clientes_por_id(clients)
    ordenados = [por_id[uid] for uid in jugadores_orden_ids if uid in por_id]
    restantes = [c for c in clients if c not in ordenados]
    ordenados.extend(restantes)
    return ordenados


def _jugador_actual_en_turno(
    game: Game, por_id: dict[int, Client]
) -> tuple[int | None, str | None, str | None]:
    """Resuelve id, nombre y color del jugador en turno.

    Returns:
        Tupla (userid, username, color_hex) o ``None`` en cada campo si no aplica.

    """
    jugador_actual_id: int | None = None
    jugador_actual_nombre: str | None = None
    jugador_actual_color: str | None = None

    try:
        turno_obj = game.turno_actual()
        if turno_obj and hasattr(turno_obj, "jugador_actual"):
            jugador_id = turno_obj.jugador_actual()
            if jugador_id:
                cliente = por_id.get(int(jugador_id))
                if cliente is not None:
                    jugador_actual_id = cliente.userid()
                    jugador_actual_nombre = cliente.username()
                    color_obj = cliente.color_actual()
                    jugador_actual_color = color_obj.to_hex() if color_obj else None
    except (AttributeError, KeyError) as e:
        LOGGER.warning("Error obteniendo información del jugador actual: %s", e)

    return jugador_actual_id, jugador_actual_nombre, jugador_actual_color


def actualizar_lista_jugadores_ui(game: Game, get_clients: GetClients) -> None:
    """Actualiza la lista de jugadores en la interfaz de todos los clientes."""
    jugadores_orden_ids = game.lista_jugadores_orden_turno()
    por_id = clientes_por_id(get_clients())

    for client in get_clients():
        jugadores_con_colores: list[tuple[int, Any]] = []
        for uid in jugadores_orden_ids:
            cliente = por_id.get(int(uid))
            if cliente is None:
                continue
            color = cliente.color_actual()
            jugadores_con_colores.append((cliente.userid(), color))
        client.transmisor.actualizar_lista_jugadores(jugadores_con_colores)


def enviar_colores_asignados(game: Game | None, get_clients: GetClients) -> None:
    """Envía los colores asignados a todos los clientes (orden de turno)."""
    clients = get_clients()
    ordenados = clientes_ordenados_por_turno(game, clients)

    for client in clients:
        for otro_client in ordenados:
            color = otro_client.color_actual()
            if color is not None:
                client.transmisor.color_asignado(otro_client.userid(), color)

    if game is not None:
        actualizar_lista_jugadores_ui(game, get_clients)


def enviar_unidades_disponibles(game: Game, get_client: GetClientById) -> None:
    """Envía las unidades disponibles al jugador del turno actual."""
    turno_actual = game.turno_actual()
    if not turno_actual:
        return

    jugador_actual_id = turno_actual.jugador_actual()
    unidades = turno_actual.unidades_por_tipo()

    cliente = get_client(int(jugador_actual_id))
    if cliente is not None:
        cliente.transmisor.enviar_unidades_disponibles(unidades)


def enviar_turno_actual(
    game: Game,
    get_clients: GetClients,
    get_client: GetClientById,
    broadcaster: ServerMessageBroadcaster,
    mapa: Mapa,
) -> None:
    """Envía turno, ronda, unidades y mapa actualizados a los clientes."""
    turno_num = game.id_turno_actual()
    por_id = clientes_por_id(get_clients())
    jugador_id, jugador_nombre, jugador_color = _jugador_actual_en_turno(game, por_id)

    for client in get_clients():
        client.transmisor.enviar_turno(
            turno_num,
            game.num_ronda(),
            jugador_id,
            jugador_nombre,
            jugador_color,
        )

    enviar_unidades_disponibles(game, get_client)
    broadcaster.enviar_mapa(mapa, game)
