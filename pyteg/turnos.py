"""Módulo para manejar los diferentes tipos de turnos del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.calculos import Calculos

if TYPE_CHECKING:
    from pyteg.server.juego.mapa import Mapa


class SiguientesTurnos:
    """Representa los turnos después del segundo turno."""

    def __init__(self, jugador: str, mapa: Mapa) -> None:
        """Inicializa un turno posterior al segundo.

        Args:
            jugador: Nombre del jugador en turno.
            mapa: Mapa del juego para calcular unidades.

        """
        self._jugador = jugador
        self._unidades = Calculos.calcular_unidades_generales(mapa, jugador)
        self._unidades_europa = Calculos.calcular_unidades_europa(mapa, jugador)
        self._unidades_africa = Calculos.calcular_unidades_africa(mapa, jugador)
        self._unidades_sudamerica = Calculos.calcular_unidades_america_del_sur(
            mapa,
            jugador,
        )
        self._unidades_norteamerica = Calculos.calcular_unidades_america_del_norte(
            mapa,
            jugador,
        )
        self._unidades_asia = Calculos.calcular_unidades_asia(mapa, jugador)
        self._unidades_oceania = Calculos.calcular_unidades_oceania(mapa, jugador)

    def unidades_por_tipo(self) -> dict[str, int]:
        """Retorna todas las unidades disponibles clasificadas por tipo/continente.

        Returns:
            Diccionario con unidades generales y bonificaciones por continente
            (solo continentes con valor > 0).

        """
        result: dict[str, int] = {"infanteria": self._unidades}
        if self._unidades_africa > 0:
            result["Africa"] = self._unidades_africa
        if self._unidades_europa > 0:
            result["Europa"] = self._unidades_europa
        if self._unidades_sudamerica > 0:
            result["América del Sur"] = self._unidades_sudamerica
        if self._unidades_norteamerica > 0:
            result["América del Norte"] = self._unidades_norteamerica
        if self._unidades_asia > 0:
            result["Asia"] = self._unidades_asia
        if self._unidades_oceania > 0:
            result["Oceanía"] = self._unidades_oceania
        return result

    def jugador_actual(self) -> str:
        """Obtiene el nombre del jugador actual.

        Returns:
            Nombre del jugador en turno.

        """
        return self._jugador

    def agregar_unidades_generales(self, num: int) -> None:
        """Agrega unidades generales disponibles.

        Args:
            num: Cantidad de unidades a agregar.

        """
        self._unidades += num

    def usar_unidad(self) -> None:
        """Consume una unidad general."""
        self._unidades -= 1

    def usar_unidad_africa(self) -> None:
        """Consume una unidad de bonificación de África."""
        self._unidades_africa -= 1

    def usar_unidad_europa(self) -> None:
        """Consume una unidad de bonificación de Europa."""
        self._unidades_europa -= 1

    def usar_unidad_oceania(self) -> None:
        """Consume una unidad de bonificación de Oceanía."""
        self._unidades_oceania -= 1

    def usar_unidad_asia(self) -> None:
        """Consume una unidad de bonificación de Asia."""
        self._unidades_asia -= 1

    def usar_unidad_sudamerica(self) -> None:
        """Consume una unidad de bonificación de Sudamérica."""
        self._unidades_sudamerica -= 1

    def usar_unidad_norteamerica(self) -> None:
        """Consume una unidad de bonificación de Norteamérica."""
        self._unidades_norteamerica -= 1

    def cant_unidades(self) -> int:
        """Obtiene la cantidad de unidades generales disponibles.

        Returns:
            Cantidad de unidades generales.

        """
        return self._unidades

    def cant_unidades_africa(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de África.

        Returns:
            Cantidad de unidades de África.

        """
        return self._unidades_africa

    def cant_unidades_europa(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de Europa.

        Returns:
            Cantidad de unidades de Europa.

        """
        return self._unidades_europa

    def cant_unidades_oceania(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de Oceanía.

        Returns:
            Cantidad de unidades de Oceanía.

        """
        return self._unidades_oceania

    def cant_unidades_asia(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de Asia.

        Returns:
            Cantidad de unidades de Asia.

        """
        return self._unidades_asia

    def cant_unidades_sudamerica(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de Sudamérica.

        Returns:
            Cantidad de unidades de Sudamérica.

        """
        return self._unidades_sudamerica

    def cant_unidades_norteamerica(self) -> int:
        """Obtiene la cantidad de unidades de bonificación de Norteamérica.

        Returns:
            Cantidad de unidades de Norteamérica.

        """
        return self._unidades_norteamerica


class SegundoTurno:
    """Representa el segundo turno de un jugador."""

    def __init__(self, jugador: str) -> None:
        """Inicializa el segundo turno.

        Args:
            jugador: Nombre del jugador en turno.

        """
        self._jugador = jugador
        self._unidades = 3

    def jugador_actual(self) -> str:
        """Obtiene el nombre del jugador actual.

        Returns:
            Nombre del jugador en turno.

        """
        return self._jugador

    def usar_unidad(self) -> None:
        """Consume una unidad."""
        self._unidades -= 1

    def cant_unidades(self) -> int:
        """Obtiene la cantidad de unidades disponibles.

        Returns:
            Cantidad de unidades.

        """
        return self._unidades

    def agregar_unidades_generales(self, num: int) -> None:
        """Agrega unidades disponibles.

        Args:
            num: Cantidad de unidades a agregar.

        """
        self._unidades += num

    def unidades_por_tipo(self) -> dict[str, int]:
        """Retorna las unidades disponibles (solo infantería en el segundo turno).

        Returns:
            Diccionario con las unidades de infantería disponibles.

        """
        return {"infanteria": self._unidades}


class PrimerTurno:
    """Representa el primer turno de un jugador."""

    def __init__(self, jugador: str) -> None:
        """Inicializa el primer turno.

        Args:
            jugador: Nombre del jugador en turno.

        """
        self._jugador = jugador
        self._unidades = 6

    def jugador_actual(self) -> str:
        """Obtiene el nombre del jugador actual.

        Returns:
            Nombre del jugador en turno.

        """
        return self._jugador

    def usar_unidad(self) -> None:
        """Consume una unidad."""
        self._unidades -= 1

    def cant_unidades(self) -> int:
        """Obtiene la cantidad de unidades disponibles.

        Returns:
            Cantidad de unidades.

        """
        return self._unidades

    def agregar_unidades_generales(self, num: int) -> None:
        """Agrega unidades disponibles.

        Args:
            num: Cantidad de unidades a agregar.

        """
        self._unidades += num

    def unidades_por_tipo(self) -> dict[str, int]:
        """Retorna las unidades disponibles (solo infantería en el primer turno).

        Returns:
            Diccionario con las unidades de infantería disponibles.

        """
        return {"infanteria": self._unidades}
