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


def descartar_refuerzos_bloqueados(mapa: Any, turno: Any, pactos: Any) -> None:
    """Descarta sólo los refuerzos sin ningún destino permitido esta vuelta.

    Las unidades generales requieren algún país propio no bloqueado; una
    bonificación continental requiere un destino en su continente. Esto evita
    exigir colocaciones imposibles antes de pasar a las acciones.
    """
    jugador = int(turno.jugador_actual())
    destinos = {
        mapa.continente(pais)
        for pais in mapa.paises()
        if mapa.jugador_posee_pais(jugador, pais)
        and not pactos.esta_bloqueado(pais, jugador)
    }
    for tipo, cantidad in turno.unidades_por_tipo().items():
        disponible = bool(destinos) if tipo == "infanteria" else tipo in destinos
        if disponible:
            continue
        for _ in range(max(0, int(cantidad))):
            if tipo == "infanteria":
                turno.usar_unidad()
            else:
                turno.usar_unidad_por_continente(tipo)
