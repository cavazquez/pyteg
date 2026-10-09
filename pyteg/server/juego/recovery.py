# ruff: noqa: SLF001
"""Sustituye sockets después de una migración sin repetir ni reordenar turnos."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyteg.server.app import Server
    from pyteg.server.conexion.cliente import Client


def reconnect_migrated(
    server: Server, client: Client, user_id: int, token: str
) -> bool:
    """Autentica una identidad recuperada y reemplaza su puerto desconectado.

    Returns:
        True si la identidad fue autenticada y su socket reemplazado.

    """
    previous = server.migration_sessions.get(user_id)
    if previous is None or not secrets.compare_digest(
        previous.reconnect_token(), token
    ):
        return False
    temporary = client.userid()
    if not server._client_registry.reasignar_cliente(temporary, user_id, client):
        return False
    client.reasignar_userid(user_id)
    client.set_reconnect_token(token)
    client.set_username(previous.username())
    client.asignar_color(previous.color_actual())
    client.import_command_cache(previous.export_command_cache())
    client.marcar_reconexion_pendiente(pendiente=False)
    game = server.game
    if game is not None:
        game._jugadores = [
            client if player.userid() == user_id else player
            for player in game._jugadores
        ]
        if user_id in game._desconectados and user_id not in game._eliminados:
            game._turn_manager.reintegrar_jugador(user_id)
            game._desconectados.discard(user_id)
    del server.migration_sessions[user_id]
    server._asignar_administrador(server._admin_user_id)
    client.transmisor.enviar_reconexion(user_id, temporary)
    client.transmisor.enviar_session_token(user_id, token)
    client.transmisor.enviar_colores(server.color.colores())
    server.enviar_username()
    server.enviar_colores_asignados()
    server.enviar_estado()
    server.enviar_configuracion_partida()
    if game is not None and game.empezo():
        server.enviar_unidades_disponibles()
    snapshot = server.public_snapshot()
    snapshot["resync"] = True
    client.transmisor.enviar_snapshot(snapshot)
    if game is not None:
        server.enviar_tarjetas_jugador(client)
        if server._game_coordinator.configuracion_partida()["objetivos_secretos"]:
            server.enviar_objetivo_secreto(client)
    return True


def finish_migration(server: Server, remaining: int | None) -> None:
    """Retoma el reloj después del plazo reservado a las reconexiones."""
    absent = list(server.migration_sessions)
    game = server.game
    turn_before = (
        game._turn_manager.clave_turno() if game is not None and game.empezo() else None
    )
    for user_id in absent:
        server._registrar_sucesion_administrador(user_id)
        game = server.game
        if game is not None and game.empezo():
            game.desconectar_jugador(user_id)
        elif game is None:
            server.color.liberar_color(
                server.migration_sessions[user_id].color_actual()
            )
            del server.migration_sessions[user_id]
    server.host_migrating = False
    if not server.estado.es_jugando():
        server._promover_administrador()
    if server.estado.es_jugando():
        server.resume_clock(
            remaining=remaining
            if game is not None and game._turn_manager.clave_turno() == turn_before
            else None,
        )
        server.enviar_turno_actual()
    server.bump_state_revision()
    server.enviar_snapshot()
