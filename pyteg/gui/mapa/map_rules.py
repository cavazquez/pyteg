"""Reglas de mapa en la GUI (adyacencia, propiedad)."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor

from pyteg.toml_reader import TomlReader

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


@lru_cache(maxsize=4)
def _adyacencias_por_tema(theme: str) -> dict[str, list[str]]:
    reader = TomlReader.from_theme(theme, strict=True)
    return dict(reader.adyacencias)


def son_adyacentes(theme: str, origen: str, destino: str) -> bool:
    """Indica si dos países son adyacentes según el tema cargado.

    Returns:
        True si destino está en la lista de adyacentes de origen.

    """
    adyacencias = _adyacencias_por_tema(theme)
    return destino in adyacencias.get(origen, [])


def _color_pais(pais_widget: Any) -> QColor | None:
    circle = getattr(pais_widget, "_circle", None)
    if circle is None:
        return None
    color = getattr(circle, "_color", None)
    if isinstance(color, QColor):
        return color
    brush_getter = getattr(circle, "brush", None)
    brush = brush_getter() if callable(brush_getter) else None
    if isinstance(brush, QBrush) and brush.style() == Qt.BrushStyle.SolidPattern:
        return brush.color()
    return None


def _snapshot_country(
    main_window: MainWindowProtocol | Any, pais: str
) -> dict[str, Any] | None:
    """Devuelve propiedad pública del servidor cuando ya hay un snapshot.

    Returns:
        Datos públicos del país, si están disponibles.

    """
    model = getattr(main_window, "client_state_model", None)
    snapshot = getattr(model, "snapshot", None)
    if not isinstance(snapshot, dict):
        return None
    countries = snapshot.get("countries")
    if not isinstance(countries, dict):
        return None
    country = countries.get(pais)
    return country if isinstance(country, dict) else None


def _snapshot_owns(
    main_window: MainWindowProtocol | Any, pais: str, userid: int
) -> bool | None:
    """Replica `jugador_posee_pais`, incluidos los países en condominio.

    Returns:
        Si el jugador ocupa el país, o None sin datos públicos.

    """
    country = _snapshot_country(main_window, pais)
    if country is None:
        return None
    if country.get("compartido") is True:
        occupants = country.get("ocupantes")
        if isinstance(occupants, list):
            return any(
                isinstance(item, dict)
                and item.get("userid") == userid
                and isinstance(item.get("unidades"), int)
                and item["unidades"] > 0
                for item in occupants
            )
    return country.get("userid") == userid


def unidades_propias_en_pais(
    main_window: MainWindowProtocol | Any, pais: str
) -> int | None:
    """Unidades del jugador local, no el total combinado de un condominio.

    Returns:
        Unidades propias, o None sin datos públicos.

    """
    client = getattr(main_window, "client", None)
    userid = client.userid() if client is not None else None
    if not userid:
        return None
    country = _snapshot_country(main_window, pais)
    if country is None:
        return None
    if country.get("compartido") is True:
        occupants = country.get("ocupantes")
        if isinstance(occupants, list):
            for item in occupants:
                if isinstance(item, dict) and item.get("userid") == int(userid):
                    units = item.get("unidades")
                    return units if isinstance(units, int) else None
        return 0
    if country.get("userid") != int(userid):
        return 0
    units = country.get("unidades")
    return units if isinstance(units, int) else None


def es_mi_pais(main_window: MainWindowProtocol | Any, pais: str) -> bool:
    """Comprueba si el país pertenece al jugador local.

    Returns:
        True si el color del país coincide con el del jugador.

    """
    client = getattr(main_window, "client", None)
    if client is None or not client.userid():
        return False

    snapshot_owns = _snapshot_owns(main_window, pais, int(client.userid()))
    if snapshot_owns is not None:
        return snapshot_owns

    colores = getattr(main_window, "colores", None)
    scene = getattr(main_window, "scene", None)
    if colores is None or scene is None or pais not in scene.paises:
        return False

    mi_color = colores.color_asignado(client.userid())
    pais_color = _color_pais(scene.paises[pais])
    if mi_color is None or pais_color is None:
        return False
    return bool(mi_color.name().lower() == pais_color.name().lower())


def es_pais_enemigo(main_window: MainWindowProtocol | Any, pais: str) -> bool:
    """Comprueba si el país es de otro jugador.

    Returns:
        True si el color del país difiere del jugador local.

    """
    client = getattr(main_window, "client", None)
    if client is None or not client.userid():
        return False

    country = _snapshot_country(main_window, pais)
    if country is not None and country.get("compartido") is True:
        occupants = country.get("ocupantes")
        if isinstance(occupants, list):
            return any(
                isinstance(item, dict)
                and isinstance(item.get("userid"), int)
                and item.get("userid") != int(client.userid())
                and isinstance(item.get("unidades"), int)
                and item["unidades"] > 0
                for item in occupants
            )
    snapshot_owns = _snapshot_owns(main_window, pais, int(client.userid()))
    if snapshot_owns is not None:
        return not snapshot_owns

    colores = getattr(main_window, "colores", None)
    scene = getattr(main_window, "scene", None)
    if colores is None or scene is None or pais not in scene.paises:
        return False

    mi_color = colores.color_asignado(client.userid())
    pais_color = _color_pais(scene.paises[pais])
    if mi_color is None or pais_color is None:
        return False
    return bool(mi_color.name().lower() != pais_color.name().lower())
