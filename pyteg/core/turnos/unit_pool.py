"""Consumo de unidades generales y bonificaciones continentales en el reparto."""

from __future__ import annotations

from typing import Any


def cant_unidades_continente(turno: Any, continente_mapa: str) -> int:
    """Unidades de bonificación disponibles para un continente del mapa.

    Returns:
        Cantidad de unidades continentales disponibles (0 si no aplica).

    """
    if hasattr(turno, "cant_unidades_por_continente"):
        return int(turno.cant_unidades_por_continente(continente_mapa))
    return 0


def unidades_disponibles_en_pais(turno: Any, continente_mapa: str) -> int:
    """Unidades que se pueden colocar en un país de ese continente.

    Returns:
        Suma de bonificación continental (si hay) más unidades generales.

    """
    generales = int(turno.cant_unidades()) if hasattr(turno, "cant_unidades") else 0
    return cant_unidades_continente(turno, continente_mapa) + generales


def consumir_unidad_reparto(turno: Any, continente_mapa: str) -> None:
    """Consume una unidad continental del país o, si no hay, una general."""
    if cant_unidades_continente(turno, continente_mapa) > 0:
        turno.usar_unidad_por_continente(continente_mapa)
        return
    turno.usar_unidad()
