"""Lógica simple de batalla.

Este módulo contiene las clases y funciones para manejar
las batallas entre países en el juego.
"""

from __future__ import annotations

from typing import TypedDict


class BattleResult(TypedDict):
    """Resultado de una batalla entre dos países.

    Attributes:
        atacante: Nombre del país atacante.
        defensor: Nombre del país defensor.
        restar: Lista de países que perdieron unidades.

    """

    atacante: str
    defensor: str
    restar: list[str]


class Batalla:
    """Clase estática para manejar batallas entre países."""

    @staticmethod
    def ataquen(
        atacante: str,
        defensor: str,
        dados_atacante: list[int],
        dados_defensor: list[int],
    ) -> BattleResult:
        """Resuelve un ataque comparando dados del atacante y defensor.

        Returns:
            Diccionario con el resultado de la batalla.

        """
        restar: list[str] = []
        resultado: BattleResult = {
            "atacante": atacante,
            "defensor": defensor,
            "restar": restar,
        }

        dados_atacante.sort(reverse=True)
        dados_defensor.sort(reverse=True)

        for combate in range(min(len(dados_atacante), len(dados_defensor))):
            if dados_defensor[combate] < dados_atacante[combate]:
                restar.append(defensor)
            else:
                restar.append(atacante)

        return resultado

    @staticmethod
    def calcular_cant_dados_atacante(cantidad: int) -> int:
        """Cantidad de dados que puede usar el atacante.

        Returns:
            Número de dados que puede usar el atacante (0-3).

        """
        return max(0, min(cantidad - 1, 3))

    @staticmethod
    def calcular_cant_dados_defensor(cantidad: int) -> int:
        """Cantidad de dados que puede usar el defensor.

        Returns:
            Número de dados que puede usar el defensor (0-3).

        """
        return max(0, min(cantidad, 3))
