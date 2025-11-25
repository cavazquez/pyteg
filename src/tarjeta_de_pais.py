"""Modelo simple de tarjeta de país con estados de asignación."""

from __future__ import annotations

from typing import Any


class TarjetaDePais:
    def __init__(self, pais: str, simbolo: str) -> None:
        self._pais = pais
        self._simbolo = simbolo
        self._usado = False
        self._jugador: Any = None

    @property
    def pais(self) -> str:
        return self._pais

    @property
    def simbolo(self) -> str:
        return self._simbolo

    def fue_usada(self) -> bool:
        return self._usado

    def jugador(self) -> Any:
        return self._jugador

    def asignar(self, jugador: Any) -> None:
        self._jugador = jugador
        self._usado = True

    def asignada(self) -> bool:
        return self._jugador is not None

    def se_puede_asignar(self) -> bool:
        return (self._jugador is None) and (self._usado is False)

    def desasignar(self) -> None:
        self._jugador = None

    def desusar(self) -> None:
        self._usado = False

    def __str__(self) -> str:
        return (
            f"pais: {self._pais}\n simbolo: {self._simbolo}\n"
            f"usado: {self._usado}\n jugador: {self._jugador}"
        )
