"""Módulo para cálculos de unidades y bonificaciones del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.config import BONIFICACIONES_CONTINENTE, COUNTRIES_DIVISOR, MIN_GENERAL_UNITS

if TYPE_CHECKING:
    from pyteg.core.combate.protocols import MapaCalculos
    from pyteg.core.partida.reglas import ThemeRules


class Calculos:
    """Clase estática para realizar cálculos de unidades y bonificaciones."""

    @staticmethod
    def calcular_unidades_generales(
        mapa: MapaCalculos,
        jugador: int,
        *,
        rules: ThemeRules | None = None,
    ) -> int:
        """Calcula unidades generales: 1 por cada N países, mínimo M.

        Returns:
            Número de unidades generales calculadas.

        """
        paises = mapa.cantidad_de_paises_del_jugador(jugador)
        divisor = rules.countries_divisor if rules is not None else COUNTRIES_DIVISOR
        minimum = rules.min_general_units if rules is not None else MIN_GENERAL_UNITS
        return max(paises // divisor, minimum)

    @staticmethod
    def calcular_unidades_continente(
        mapa: MapaCalculos,
        jugador: int,
        continente: str,
        *,
        bonuses: dict[str, int] | None = None,
    ) -> int:
        """Calcula bonificación por control completo de un continente.

        Args:
            mapa: Instancia del mapa del juego.
            jugador: userid (int) del jugador.
            continente: ID del continente en el mapa (TOML), ej. ``Sudamerica``.
            bonuses: Bonos por continente del perfil activo.

        Returns:
            Unidades de bonificación (0 si no controla el continente).

        """
        continent_bonuses = bonuses or BONIFICACIONES_CONTINENTE
        if continente not in continent_bonuses:
            return 0

        if mapa.jugador_controla_continente(jugador, continente):
            return continent_bonuses[continente]
        return 0
