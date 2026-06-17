"""Estado de gameplay en la GUI (turno, habilitación de acciones)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


def es_mi_turno(main_window: MainWindowProtocol | Any) -> bool:
    """Indica si el jugador local tiene el turno activo.

    Returns:
        True si el userid local coincide con el jugador en turno.

    """
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
    """Actualiza toolbar según turno, fase y selección."""
    from pyteg.gui.toolbar import ToolBar  # noqa: PLC0415

    mi_turno = es_mi_turno(main_window)
    acciones_combate = puede_atacar_o_mover(main_window)
    scene = getattr(main_window, "scene", None)
    hay_dos_paises = False
    if scene is not None and hasattr(scene, "selection_manager"):
        sm = scene.selection_manager
        hay_dos_paises = (
            sm.get_pais_origen() is not None and sm.get_pais_destino() is not None
        )

    if hasattr(main_window, "findChildren"):
        for toolbar in main_window.findChildren(ToolBar):
            if hasattr(toolbar, "actualizar_botones_seleccion"):
                toolbar.actualizar_botones_seleccion(
                    hay_dos_paises_seleccionados=hay_dos_paises and acciones_combate
                )
            if hasattr(toolbar, "actualizar_botones_turno"):
                toolbar.actualizar_botones_turno(es_mi_turno=mi_turno)
