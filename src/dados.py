from __future__ import annotations

from random import choices


class Dados:
    @staticmethod
    def tirar_dados(cant: int) -> list[int]:
        return choices(range(1, 7), k=cant)  # noqa: S311

    @staticmethod
    def tirar_dados_ordenados(cant: int) -> list[int]:
        return sorted(choices(range(1, 7), k=cant), reverse=True)  # noqa: S311
