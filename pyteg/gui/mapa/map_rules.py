"""Reglas de mapa en la GUI (adyacencia, propiedad)."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor

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
    return None


def es_mi_pais(main_window: MainWindowProtocol | Any, pais: str) -> bool:
    """Comprueba si el país pertenece al jugador local.

    Returns:
        True si el color del país coincide con el del jugador.

    """
    client = getattr(main_window, "client", None)
    if client is None or not client.userid():
        return False

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

    colores = getattr(main_window, "colores", None)
    scene = getattr(main_window, "scene", None)
    if colores is None or scene is None or pais not in scene.paises:
        return False

    mi_color = colores.color_asignado(client.userid())
    pais_color = _color_pais(scene.paises[pais])
    if mi_color is None or pais_color is None:
        return False
    return bool(mi_color.name().lower() != pais_color.name().lower())
