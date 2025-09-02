from typing import ClassVar

from src.server_mapa import Mapa


class Calculos:
    # Bonificaciones por control completo de continente
    BONIFICACIONES_CONTINENTE: ClassVar[dict[str, int]] = {
        "Europa": 5,
        "Asia": 7,
        "Africa": 3,
        "Oceania": 2,
        "Sudamerica": 3,
        "Norteamerica": 5,
    }

    # Constantes para cálculo de unidades generales
    UNIDADES_MINIMAS = 3
    DIVISOR_PAISES = 2

    @staticmethod
    def calcular_unidades_generales(mapa: Mapa, jugador: str) -> int:
        """Calcula unidades generales: 1 por cada 2 países, mínimo 3."""
        paises = mapa.cantidad_de_paises_del_jugador(jugador)
        return max(paises // Calculos.DIVISOR_PAISES, Calculos.UNIDADES_MINIMAS)

    @staticmethod
    def calcular_unidades_continente(mapa: Mapa, jugador: str, continente: str) -> int:
        """Calcula bonificación por control completo de un continente.

        Args:
            mapa: Instancia del mapa del juego
            jugador: ID del jugador
            continente: Nombre del continente

        Returns:
            int: Unidades de bonificación (0 si no controla el continente)
        """
        if continente not in Calculos.BONIFICACIONES_CONTINENTE:
            return 0

        if mapa.jugador_controla_continente(jugador, continente):
            return Calculos.BONIFICACIONES_CONTINENTE[continente]
        return 0

    @staticmethod
    def calcular_unidades_europa(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Europa")

    @staticmethod
    def calcular_unidades_asia(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Asia")

    @staticmethod
    def calcular_unidades_africa(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Africa")

    @staticmethod
    def calcular_unidades_oceania(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Oceania")

    @staticmethod
    def calcular_unidades_america_del_sur(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Sudamerica")

    @staticmethod
    def calcular_unidades_america_del_norte(mapa: Mapa, jugador: str) -> int:
        return Calculos.calcular_unidades_continente(mapa, jugador, "Norteamerica")
