"""Sistema de misiles para el juego.

Este módulo encapsula toda la lógica relacionada con misiles,
separándola de la clase Mapa para mejorar la separación de responsabilidades.
"""

from collections import deque
from typing import TYPE_CHECKING

from pyteg.config import (
    MISSILE_DAMAGE_DISTANCE_1,
    MISSILE_DAMAGE_DISTANCE_2,
    MISSILE_DAMAGE_DISTANCE_3,
)

if TYPE_CHECKING:
    from pyteg.server.juego.mapa import Mapa


class MissileSystem:
    """Sistema para gestionar misiles en el mapa del juego."""

    def __init__(self, mapa: "Mapa") -> None:
        """Inicializa el sistema de misiles.

        Args:
            mapa: Referencia al mapa del juego.

        """
        self._mapa = mapa

    def agregar_misil(self, pais: str) -> None:
        """Agrega un misil al país especificado.

        Args:
            pais: Nombre del país donde se agregará el misil.

        """
        self._mapa._incrementar_misiles(pais)  # noqa: SLF001

    def cantidad_misiles(self, pais: str) -> int:
        """Retorna la cantidad de misiles en el país especificado.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de misiles en el país.

        """
        return self._mapa._obtener_misiles(pais)  # noqa: SLF001

    def usar_misil(self, pais: str) -> None:
        """Usa un misil del país especificado (lo decrementa en 1).

        Args:
            pais: Nombre del país desde donde se lanzará el misil.

        """
        self._mapa._decrementar_misiles(pais)  # noqa: SLF001

    def calcular_distancia(self, pais_origen: str, pais_destino: str) -> int:
        """Calcula la distancia mínima entre dos países usando BFS.

        Args:
            pais_origen: País de origen.
            pais_destino: País de destino.

        Returns:
            Distancia mínima en saltos entre países, o -1 si no hay camino.

        """
        if not self._mapa._tiene_pais(pais_origen) or not self._mapa._tiene_pais(  # noqa: SLF001
            pais_destino
        ):
            return -1

        if pais_origen == pais_destino:
            return 0

        # BFS para encontrar la distancia mínima
        visitados = {pais_origen}
        cola: deque[tuple[str, int]] = deque([(pais_origen, 0)])

        while cola:
            pais_actual, distancia = cola.popleft()

            for pais_adyacente in self._mapa.obtener_paises_adyacentes(pais_actual):
                if pais_adyacente == pais_destino:
                    return distancia + 1

                if pais_adyacente not in visitados:
                    visitados.add(pais_adyacente)
                    cola.append((pais_adyacente, distancia + 1))

        return -1  # No hay camino

    def calcular_dano_misil(self, distancia: int) -> int:
        """Calcula el daño que causa un misil según la distancia.

        Args:
            distancia: Distancia en saltos entre países.

        Returns:
            Cantidad de unidades de daño (3, 2, 1, o 0 si fuera de rango).

        """
        damage_map = {
            1: MISSILE_DAMAGE_DISTANCE_1,
            2: MISSILE_DAMAGE_DISTANCE_2,
            3: MISSILE_DAMAGE_DISTANCE_3,
        }
        return damage_map.get(distancia, 0)  # 0 si está fuera de rango
