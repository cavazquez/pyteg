"""Módulo para manejar el mazo de tarjetas del juego."""

from __future__ import annotations

from collections import Counter
from itertools import cycle
from random import sample
from typing import TYPE_CHECKING, Any

from src.config import CARDS_FOR_EXCHANGE, MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE
from src.tarjeta_de_pais import TarjetaDePais

if TYPE_CHECKING:
    from collections.abc import Callable


class Mazo:
    """Representa el mazo de tarjetas de países."""

    def __init__(self, paises: list[str], simbolos: list[str]) -> None:
        """Inicializa el mazo con tarjetas de países.

        Args:
            paises: Lista de nombres de países.
            simbolos: Lista de símbolos para las tarjetas.

        """
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo: dict[str, TarjetaDePais] = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta.pais] = tarjeta

    def build_tarjetas_de_paises(
        self, paises: list[str], simbolos: list[str]
    ) -> list[TarjetaDePais]:
        """Construye tarjetas de países con símbolos cíclicos.

        Args:
            paises: Lista de nombres de países.
            simbolos: Lista de símbolos (se repiten cíclicamente).

        Returns:
            Lista de tarjetas de países.

        """
        return list(map(TarjetaDePais, paises, cycle(simbolos)))

    def cantidad_tarjetas(self) -> int:
        """Obtiene la cantidad total de tarjetas.

        Returns:
            Cantidad total de tarjetas.

        """
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self) -> int:
        """Obtiene la cantidad de tarjetas usadas.

        Returns:
            Cantidad de tarjetas usadas.

        """
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.fue_usada() is True)

    def cantidad_tarjetas_asignadas(self) -> int:
        """Obtiene la cantidad de tarjetas asignadas.

        Returns:
            Cantidad de tarjetas asignadas.

        """
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.asignada() is True)

    def tarjetas(self) -> list[TarjetaDePais]:
        """Obtiene todas las tarjetas del mazo.

        Returns:
            Lista de todas las tarjetas.

        """
        return list(self.mazo.values())

    def tarjetas_asignadas(self, jugador: Any) -> list[TarjetaDePais]:
        """Obtiene las tarjetas asignadas a un jugador.

        Args:
            jugador: Jugador del que obtener las tarjetas.

        Returns:
            Lista de tarjetas asignadas al jugador.

        """
        return [tarjeta for tarjeta in self.tarjetas() if tarjeta.jugador() == jugador]

    def cant_tarjetas_asignadas(self, jugador: Any) -> int:
        """Obtiene la cantidad de tarjetas asignadas a un jugador.

        Args:
            jugador: Jugador del que contar las tarjetas.

        Returns:
            Cantidad de tarjetas asignadas al jugador.

        """
        return sum(1 for tarjeta in self.tarjetas_asignadas(jugador))

    def simbolo_asignado_almenos_3_tarjetas(
        self, jugador: Any
    ) -> list[tuple[str, int]]:
        """Obtiene el símbolo más común de las tarjetas del jugador.

        Args:
            jugador: Jugador del que obtener el símbolo.

        Returns:
            Lista con tupla (símbolo, cantidad) del símbolo más común.

        """
        return Counter(
            [tarjeta.simbolo for tarjeta in self.tarjetas_asignadas(jugador)],
        ).most_common(1)

    def dame_3_tarjetas_para_canje(self, jugador: Any) -> list[TarjetaDePais]:
        """Obtiene 3 tarjetas para canje de un jugador.

        Si tiene 3 o más del mismo símbolo, retorna 3 de ese símbolo.
        Si no, retorna 3 tarjetas con símbolos diferentes.

        Args:
            jugador: Jugador del que obtener las tarjetas.

        Returns:
            Lista de 3 tarjetas para canje.

        """
        simbolo = self.simbolo_asignado_almenos_3_tarjetas(jugador)[0]
        if simbolo[1] >= MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE:
            return [
                tarjeta
                for tarjeta in self.tarjetas_asignadas(jugador)
                if tarjeta.simbolo == simbolo[0]
            ][:CARDS_FOR_EXCHANGE]
        acum: set[str] = set()
        res: list[TarjetaDePais] = []
        for tarjeta in self.tarjetas_asignadas(jugador):
            simbolo_tarjeta = tarjeta.simbolo
            if simbolo_tarjeta not in acum:
                res.append(tarjeta)
                acum.add(simbolo_tarjeta)
        return res[:3]

    def dame_simbolos(self) -> set[str]:
        """Obtiene todos los símbolos únicos del mazo.

        Returns:
            Conjunto de símbolos únicos.

        """
        return {tarjeta.simbolo for tarjeta in self.tarjetas()}

    def liberar_tarjetas_usadas(self) -> None:
        """Libera las tarjetas usadas que no están asignadas."""
        for tarjeta in self.tarjetas():
            if tarjeta.fue_usada() and not tarjeta.asignada():
                tarjeta.desusar()

    def asignar_tarjeta(
        self,
        jugador: Any,
        mezclar: Callable[[list[TarjetaDePais], int], list[TarjetaDePais]] = sample,
    ) -> TarjetaDePais | None:
        """Asigna una tarjeta disponible a un jugador.

        Args:
            jugador: Jugador al que asignar la tarjeta.
            mezclar: Función para mezclar las tarjetas (por defecto sample).

        Returns:
            La tarjeta asignada o None si no hay tarjetas disponibles.

        """
        if self.cantidad_tarjetas_usadas() == self.cantidad_tarjetas():
            self.liberar_tarjetas_usadas()
        tarjetas = mezclar(self.tarjetas(), self.cantidad_tarjetas())
        for tarjeta in tarjetas:
            if tarjeta.se_puede_asignar():
                tarjeta.asignar(jugador)
                return tarjeta
        return None

    def desasignar_tarjetas(self, tarjetas: list[TarjetaDePais]) -> None:
        """Desasigna una lista de tarjetas.

        Args:
            tarjetas: Lista de tarjetas a desasignar.

        """
        for tarjeta in tarjetas:
            tarjeta.desasignar()

    def __str__(self) -> str:
        """Retorna representación en string del mazo.

        Returns:
            String con los nombres de los países del mazo.

        """
        res = ""
        for elem in self.mazo:
            res = res + elem + "\n"
        return res
