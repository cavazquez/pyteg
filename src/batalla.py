"""Lógica simple de batalla."""

from __future__ import annotations

from typing import TypedDict


class BattleResult(TypedDict):
    atacante: str
    defensor: str
    restar: list[str]


class Batalla:
    @staticmethod
    def ataquen(
        atacante: str,
        defensor: str,
        dados_atacante: list[int],
        dados_defensor: list[int],
    ) -> BattleResult:
        """Resuelve un ataque comparando dados del atacante y defensor."""
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
        """Cantidad de dados que puede usar el atacante."""
        return max(0, min(cantidad - 1, 3))

    @staticmethod
    def calcular_cant_dados_defensor(cantidad: int) -> int:
        """Cantidad de dados que puede usar el defensor."""
        return max(0, min(cantidad, 3))
