from __future__ import annotations

from collections import Counter
from itertools import cycle
from random import sample
from typing import TYPE_CHECKING, Any

from src.tarjeta_de_pais import TarjetaDePais

if TYPE_CHECKING:
    from collections.abc import Callable


class Mazo:
    def __init__(self, paises: list[str], simbolos: list[str]) -> None:
        tarjetas = self.build_tarjetas_de_paises(paises, simbolos)
        self.mazo: dict[str, TarjetaDePais] = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta.pais] = tarjeta

    def build_tarjetas_de_paises(
        self, paises: list[str], simbolos: list[str]
    ) -> list[TarjetaDePais]:
        return list(map(TarjetaDePais, paises, cycle(simbolos)))

    def cantidad_tarjetas(self) -> int:
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self) -> int:
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.fue_usada() is True)

    def cantidad_tarjetas_asignadas(self) -> int:
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.asignada() is True)

    def tarjetas(self) -> list[TarjetaDePais]:
        return list(self.mazo.values())

    def tarjetas_asignadas(self, jugador: Any) -> list[TarjetaDePais]:
        return [tarjeta for tarjeta in self.tarjetas() if tarjeta.jugador() == jugador]

    def cant_tarjetas_asignadas(self, jugador: Any) -> int:
        return sum(1 for tarjeta in self.tarjetas_asignadas(jugador))

    def simbolo_asignado_almenos_3_tarjetas(
        self, jugador: Any
    ) -> list[tuple[str, int]]:
        return Counter(
            [tarjeta.simbolo for tarjeta in self.tarjetas_asignadas(jugador)],
        ).most_common(1)

    def dame_3_tarjetas_para_canje(self, jugador: Any) -> list[TarjetaDePais]:
        simbolo = self.simbolo_asignado_almenos_3_tarjetas(jugador)[0]
        if simbolo[1] >= 3:
            return [
                tarjeta
                for tarjeta in self.tarjetas_asignadas(jugador)
                if tarjeta.simbolo == simbolo[0]
            ][:3]
        acum: set[str] = set()
        res: list[TarjetaDePais] = []
        for tarjeta in self.tarjetas_asignadas(jugador):
            simbolo_tarjeta = tarjeta.simbolo
            if simbolo_tarjeta not in acum:
                res.append(tarjeta)
                acum.add(simbolo_tarjeta)
        return res[:3]

    def dame_simbolos(self) -> set[str]:
        return {tarjeta.simbolo for tarjeta in self.tarjetas()}

    def liberar_tarjetas_usadas(self) -> None:
        for tarjeta in self.tarjetas():
            if tarjeta.fue_usada() and not tarjeta.asignada():
                tarjeta.desusar()

    def asignar_tarjeta(
        self,
        jugador: Any,
        mezclar: Callable[[list[TarjetaDePais], int], list[TarjetaDePais]] = sample,
    ) -> TarjetaDePais | None:
        if self.cantidad_tarjetas_usadas() == self.cantidad_tarjetas():
            self.liberar_tarjetas_usadas()
        tarjetas = mezclar(self.tarjetas(), self.cantidad_tarjetas())
        for tarjeta in tarjetas:
            if tarjeta.se_puede_asignar():
                tarjeta.asignar(jugador)
                return tarjeta
        return None

    def desasignar_tarjetas(self, tarjetas: list[TarjetaDePais]) -> None:
        for tarjeta in tarjetas:
            tarjeta.desasignar()

    def __str__(self) -> str:
        res = ""
        for elem in self.mazo:
            res = res + elem + "\n"
        return res
