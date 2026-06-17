"""Módulo para cálculos de unidades y bonificaciones del juego."""

from pyteg.config import BONIFICACIONES_CONTINENTE, COUNTRIES_DIVISOR, MIN_GENERAL_UNITS
from pyteg.core.combate.protocols import MapaCalculos


class Calculos:
    """Clase estática para realizar cálculos de unidades y bonificaciones."""

    @staticmethod
    def calcular_unidades_generales(mapa: MapaCalculos, jugador: int) -> int:
        """Calcula unidades generales: 1 por cada N países, mínimo M.

        Returns:
            Número de unidades generales calculadas.

        """
        paises = mapa.cantidad_de_paises_del_jugador(jugador)
        return max(paises // COUNTRIES_DIVISOR, MIN_GENERAL_UNITS)

    @staticmethod
    def calcular_unidades_continente(
        mapa: MapaCalculos, jugador: int, continente: str
    ) -> int:
        """Calcula bonificación por control completo de un continente.

        Args:
            mapa: Instancia del mapa del juego.
            jugador: userid (int) del jugador.
            continente: ID del continente en el mapa (TOML), ej. ``Sudamerica``.

        Returns:
            Unidades de bonificación (0 si no controla el continente).

        """
        if continente not in BONIFICACIONES_CONTINENTE:
            return 0

        if mapa.jugador_controla_continente(jugador, continente):
            return BONIFICACIONES_CONTINENTE[continente]
        return 0
