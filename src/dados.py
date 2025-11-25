"""Módulo para simular tiradas de dados."""

from __future__ import annotations

from random import choices


class Dados:
    """Clase para simular tiradas de dados de 6 caras."""

    @staticmethod
    def tirar_dados(cant: int) -> list[int]:
        """Tira una cantidad de dados y retorna los valores.

        Args:
            cant: Cantidad de dados a tirar.

        Returns:
            Lista con los valores obtenidos (1-6).

        """
        return choices(range(1, 7), k=cant)  # noqa: S311

    @staticmethod
    def tirar_dados_ordenados(cant: int) -> list[int]:
        """Tira una cantidad de dados y retorna los valores ordenados descendente.

        Args:
            cant: Cantidad de dados a tirar.

        Returns:
            Lista con los valores obtenidos (1-6) ordenados de mayor a menor.

        """
        return sorted(choices(range(1, 7), k=cant), reverse=True)  # noqa: S311
