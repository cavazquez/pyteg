"""Módulo para cálculos de unidades y bonificaciones del juego."""

from typing import ClassVar

from pyteg.config import COUNTRIES_DIVISOR, MIN_GENERAL_UNITS
from pyteg.core.combate.protocols import MapaCalculos


class Calculos:
    """Clase estática para realizar cálculos de unidades y bonificaciones."""

    # Bonificaciones por control completo de continente
    BONIFICACIONES_CONTINENTE: ClassVar[dict[str, int]] = {
        "Europa": 5,
        "Asia": 7,
        "Africa": 3,
        "Oceania": 2,
        "Sudamerica": 3,
        "Norteamerica": 5,
    }

    @staticmethod
    def calcular_unidades_generales(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula unidades generales: 1 por cada N países, mínimo M.

        Returns:
            Número de unidades generales calculadas.

        """
        paises = mapa.cantidad_de_paises_del_jugador(jugador)
        return max(paises // COUNTRIES_DIVISOR, MIN_GENERAL_UNITS)

    @staticmethod
    def calcular_unidades_continente(
        mapa: MapaCalculos, jugador: str, continente: str
    ) -> int:
        """Calcula bonificación por control completo de un continente.

        Args:
            mapa: Instancia del mapa del juego
            jugador: ID del jugador
            continente: Nombre del continente

        Returns:
            Unidades de bonificación (0 si no controla el continente).

        """
        if continente not in Calculos.BONIFICACIONES_CONTINENTE:
            return 0

        if mapa.jugador_controla_continente(jugador, continente):
            return Calculos.BONIFICACIONES_CONTINENTE[continente]
        return 0

    @staticmethod
    def calcular_unidades_europa(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de Europa.

        Returns:
            Unidades de bonificación por Europa.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Europa")

    @staticmethod
    def calcular_unidades_asia(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de Asia.

        Returns:
            Unidades de bonificación por Asia.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Asia")

    @staticmethod
    def calcular_unidades_africa(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de África.

        Returns:
            Unidades de bonificación por África.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Africa")

    @staticmethod
    def calcular_unidades_oceania(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de Oceanía.

        Returns:
            Unidades de bonificación por Oceanía.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Oceania")

    @staticmethod
    def calcular_unidades_america_del_sur(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de Sudamérica.

        Returns:
            Unidades de bonificación por Sudamérica.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Sudamerica")

    @staticmethod
    def calcular_unidades_america_del_norte(mapa: MapaCalculos, jugador: str) -> int:
        """Calcula bonificación por control completo de Norteamérica.

        Returns:
            Unidades de bonificación por Norteamérica.

        """
        return Calculos.calcular_unidades_continente(mapa, jugador, "Norteamerica")
