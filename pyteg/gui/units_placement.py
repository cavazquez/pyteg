"""Disponibilidad de unidades para colocar en un país (GUI)."""

from __future__ import annotations

from pyteg.config import MAP_CONTINENT_TO_PANEL_LABEL
from pyteg.i18n import translate as _


def unidades_colocables_en_pais(
    last_units: dict[str, int], continente_mapa: str
) -> tuple[int, int, int]:
    """Unidades que se pueden colocar en un país del continente dado.

    Replica la lógica del servidor (`unidades_disponibles_en_pais`): bonificación
    continental del país más unidades generales.

    Returns:
        Tupla ``(total, continentales, generales)``.

    """
    generales = int(last_units.get("Generales", 0))
    panel_key = MAP_CONTINENT_TO_PANEL_LABEL.get(continente_mapa)
    continentales = int(last_units.get(panel_key, 0)) if panel_key else 0
    return continentales + generales, continentales, generales


def tooltip_colocar_unidad(last_units: dict[str, int], continente_mapa: str) -> str:
    """Texto de ayuda para la acción de colocar unidad en el menú contextual.

    Returns:
        Tooltip traducible según bonificación continental y generales.

    """
    total, continentales, generales = unidades_colocables_en_pais(
        last_units, continente_mapa
    )
    if total <= 0:
        return _("Sin unidades disponibles para este país")

    panel_key = MAP_CONTINENT_TO_PANEL_LABEL.get(continente_mapa)
    if continentales > 0 and generales > 0 and panel_key:
        return _("Consume primero refuerzos de {} ({}), luego generales ({})").format(
            _(panel_key), continentales, generales
        )
    if continentales > 0 and panel_key:
        return _("Refuerzos de {}: {} disponibles").format(_(panel_key), continentales)
    return _("Unidades generales: {} disponibles").format(generales)
