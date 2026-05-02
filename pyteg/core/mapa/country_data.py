"""Estructura de datos tipada para países.

Este módulo proporciona estructuras de datos tipadas para representar
países en el mapa, mejorando type safety y legibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Índices para la estructura de datos del país (compatibilidad con formato antiguo)
_IDX_UNIDADES = 0
_IDX_CONTINENTE = 1
_IDX_JUGADOR = 2
_IDX_ADYACENTES = 3
_IDX_MISILES = 4


@dataclass
class CountryData:
    """Datos de un país en el mapa.

    Attributes:
        unidades: Cantidad de unidades en el país.
        continente: Nombre del continente al que pertenece.
        jugador: ID del jugador que posee el país (None si no está asignado).
        adyacentes: Lista de países adyacentes.
        misiles: Cantidad de misiles en el país.

    """

    unidades: int = 1
    continente: str = ""
    jugador: str | None = None
    adyacentes: list[str] = field(default_factory=list)
    misiles: int = 0

    def to_list(self) -> list[int | str | list[str] | None]:
        """Convierte los datos del país a la estructura de lista original.

        Returns:
            Lista con los datos en el formato:
            [unidades, continente, jugador, adyacentes, misiles]

        """
        return [
            self.unidades,
            self.continente,
            self.jugador,
            self.adyacentes,
            self.misiles,
        ]

    @classmethod
    def from_list(cls, data: list[Any]) -> CountryData:
        """Crea un CountryData desde la estructura de lista original.

        Args:
            data: Lista con los datos en el formato:
            [unidades, continente, jugador, adyacentes, misiles]

        Returns:
            Instancia de CountryData.

        """
        unidades = int(data[_IDX_UNIDADES]) if len(data) > _IDX_UNIDADES else 1
        continente = str(data[_IDX_CONTINENTE]) if len(data) > _IDX_CONTINENTE else ""
        jugador = (
            data[_IDX_JUGADOR]
            if len(data) > _IDX_JUGADOR and data[_IDX_JUGADOR] is not None
            else None
        )
        adyacentes = list(data[_IDX_ADYACENTES]) if len(data) > _IDX_ADYACENTES else []
        misiles = int(data[_IDX_MISILES]) if len(data) > _IDX_MISILES else 0

        return cls(
            unidades=unidades,
            continente=continente,
            jugador=jugador,
            adyacentes=adyacentes,
            misiles=misiles,
        )
