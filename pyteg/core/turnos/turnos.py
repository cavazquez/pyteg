"""Módulo para manejar los diferentes tipos de turnos del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.config import CONTINENT_UNIT_SUFFIX, CONTINENTS
from pyteg.core.combate.calculos import Calculos

if TYPE_CHECKING:
    from pyteg.server.juego.mapa import Mapa


class SiguientesTurnos:
    """Representa los turnos después del segundo turno."""

    def __init__(self, jugador: int, mapa: Mapa) -> None:
        """Inicializa un turno posterior al segundo.

        Args:
            jugador: userid (int) del jugador en turno.
            mapa: Mapa del juego para calcular unidades.

        """
        self._jugador = jugador
        self._unidades = Calculos.calcular_unidades_generales(mapa, jugador)
        for spec in CONTINENTS:
            cantidad = Calculos.calcular_unidades_continente(mapa, jugador, spec.map_id)
            setattr(self, f"_unidades_{spec.unit_suffix}", cantidad)

    def unidades_por_tipo(self) -> dict[str, int]:
        """Retorna todas las unidades disponibles clasificadas por tipo/continente.

        Returns:
            Diccionario con unidades generales y bonificaciones por continente
            (solo continentes con valor > 0).

        """
        result: dict[str, int] = {"infanteria": self._unidades}
        for spec in CONTINENTS:
            cantidad = getattr(self, f"_unidades_{spec.unit_suffix}", 0)
            if cantidad > 0:
                result[spec.map_id] = cantidad
        return result

    def jugador_actual(self) -> int:
        """Obtiene el userid del jugador actual.

        Returns:
            userid (int) del jugador en turno.

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

    def cant_unidades_por_continente(self, map_id: str) -> int:
        """Unidades de bonificación disponibles para un continente del mapa.

        Args:
            map_id: ID del continente (TOML), ej. ``Africa``.

        Returns:
            Cantidad de unidades continentales disponibles.

        """
        suffix = CONTINENT_UNIT_SUFFIX.get(map_id)
        if suffix is None:
            return 0
        return int(getattr(self, f"_unidades_{suffix}", 0))

    def usar_unidad_por_continente(self, map_id: str) -> None:
        """Consume una unidad de bonificación del continente indicado."""
        suffix = CONTINENT_UNIT_SUFFIX[map_id]
        attr = f"_unidades_{suffix}"
        setattr(self, attr, getattr(self, attr) - 1)

    def cant_unidades(self) -> int:
        """Obtiene la cantidad de unidades generales disponibles.

        Returns:
            Cantidad de unidades generales.

        """
        return self._unidades


class SegundoTurno:
    """Representa el segundo turno de un jugador."""

    def __init__(self, jugador: int) -> None:
        """Inicializa el segundo turno.

        Args:
            jugador: userid (int) del jugador en turno.

        """
        self._jugador = jugador
        self._unidades = 3

    def jugador_actual(self) -> int:
        """Obtiene el userid del jugador actual.

        Returns:
            userid (int) del jugador en turno.

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

    def __init__(self, jugador: int) -> None:
        """Inicializa el primer turno.

        Args:
            jugador: userid (int) del jugador en turno.

        """
        self._jugador = jugador
        self._unidades = 6

    def jugador_actual(self) -> int:
        """Obtiene el userid del jugador actual.

        Returns:
            userid (int) del jugador en turno.

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
