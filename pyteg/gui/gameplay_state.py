"""Estado de gameplay en la GUI (turno, habilitación de acciones)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


_FASES_MOSTRABLES = {
    "colocacion": "Colocación",
    "acciones": "Acciones",
}


def texto_fase(fase: str | None) -> str:
    """Convierte el identificador de fase del protocolo en texto de UI.

    Returns:
        Nombre de la fase traducido para mostrar al usuario.

    """
    if fase is None:
        return _("Acciones")
    return _(_FASES_MOSTRABLES.get(fase, fase.capitalize()))


def contexto_partida(main_window: MainWindowProtocol | Any) -> str | None:
    """Devuelve el contexto compacto que se muestra en la barra de estado.

    La barra conserva el estado global (conectado, esperando o finalizado) y
    agrega este contexto solamente mientras hay una partida en curso. De esa
    forma una fase vieja no queda visible después de desconectar al cliente.

    Returns:
        Texto compacto del contexto, o ``None`` si solo corresponde mostrar
        el estado global.

    """
    if getattr(main_window, "partida_finalizada", False) is True:
        return None

    estado = getattr(main_window, "estado_actual", None)
    fase = getattr(main_window, "fase_actual", None)
    if estado not in {None, "", "JUGANDO"}:
        return None

    jugador = getattr(main_window, "jugador_actual_nombre", None)
    if not jugador:
        jugador_id = getattr(main_window, "jugador_actual_id", None)
        jugador = _("Jugador {}").format(jugador_id) if jugador_id else _("Sin turno")

    try:
        pendientes = max(
            0, int(getattr(main_window, "unidades_pendientes_servidor", 0))
        )
    except TypeError, ValueError:
        pendientes = 0

    contexto = _("Fase: {} · Activo: {} · Refuerzos: {}").format(
        texto_fase(fase),
        jugador,
        pendientes,
    )
    situacion = _situacion_activa(main_window)
    if situacion is not None:
        contexto += _(" · Situación: {}").format(situacion)
    return contexto


def _situacion_activa(main_window: MainWindowProtocol | Any) -> str | None:
    """Obtiene el nombre público de la situación desde el snapshot.

    Returns:
        Nombre visible o ``None`` cuando no hay situación activa.

    """
    model = getattr(main_window, "client_state_model", None)
    snapshot = getattr(model, "snapshot", None)
    if not isinstance(snapshot, dict):
        return None
    situacion = snapshot.get("situacion")
    if not isinstance(situacion, dict):
        return None
    identifier = situacion.get("id")
    name = situacion.get("nombre")
    if identifier in {None, "", "none"} or not isinstance(name, str):
        return None
    return name


def es_mi_turno(main_window: MainWindowProtocol | Any) -> bool:
    """Indica si el jugador local tiene el turno activo.

    Returns:
        True si el userid local coincide con el jugador en turno.

    """
    if getattr(main_window, "partida_finalizada", False) is True:
        return False

    client = getattr(main_window, "client", None)
    if client is None:
        return False
    userid = client.userid() if hasattr(client, "userid") else None
    jugador_actual_id = getattr(main_window, "jugador_actual_id", None)
    if not userid or jugador_actual_id is None:
        return False
    return int(userid) == int(jugador_actual_id)


def en_fase_reparto(main_window: MainWindowProtocol | Any) -> bool:
    """Comprueba si quedan unidades por colocar.

    Returns:
        True durante la fase de refuerzos.

    """
    fase_actual = getattr(main_window, "fase_actual", None)
    if fase_actual is not None:
        return (
            fase_actual == "colocacion"
            and int(getattr(main_window, "unidades_pendientes_servidor", 0)) > 0
        )
    last_units = getattr(main_window, "last_units", {})
    if not last_units:
        return False
    if int(last_units.get("Generales", 0)) > 0:
        return True
    for key, value in last_units.items():
        if key in {"Generales", "Misiles"}:
            continue
        if int(value) > 0:
            return True
    return False


def puede_atacar_o_mover(main_window: MainWindowProtocol | Any) -> bool:
    """Comprueba si el jugador puede atacar o mover.

    Returns:
        True en turno propio y sin reparto pendiente.

    """
    return es_mi_turno(main_window) and not en_fase_reparto(main_window)


def avisar_fuera_de_turno(main_window: MainWindowProtocol | Any) -> None:
    """Muestra mensaje en la barra de estado si no es el turno del jugador."""
    if hasattr(main_window, "update_status_bar"):
        main_window.update_status_bar(_("No es tu turno"), "orange")


def avisar_fase_reparto(main_window: MainWindowProtocol | Any) -> None:
    """Muestra mensaje si aún hay unidades por colocar."""
    if hasattr(main_window, "update_status_bar"):
        main_window.update_status_bar(
            _("Colocá todas las unidades antes de atacar o mover"), "orange"
        )


def refresh_acciones_juego(main_window: MainWindowProtocol | Any) -> None:
    """Actualiza toolbar y contexto desde la disponibilidad compartida."""
    from pyteg.gui.action_availability import selection_availability  # noqa: PLC0415
    from pyteg.gui.toolbar import ToolBar  # noqa: PLC0415

    availability = selection_availability(main_window)

    scene = getattr(main_window, "scene", None)
    selection_manager = getattr(scene, "selection_manager", None)
    render_selection = getattr(selection_manager, "render_selection_label", None)
    if callable(render_selection):
        render_selection(availability)

    if hasattr(main_window, "findChildren"):
        for toolbar in main_window.findChildren(ToolBar):
            toolbar.aplicar_disponibilidad(availability)

    status_manager = getattr(main_window, "status_manager", None)
    update_context = getattr(status_manager, "update_gameplay_context", None)
    if callable(update_context):
        update_context()
