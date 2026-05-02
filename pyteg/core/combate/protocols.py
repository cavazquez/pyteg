"""Protocolos estructurales del módulo de combate.

Permite que `core.combate.calculos` opere sobre cualquier objeto que cumpla la
interfaz mínima requerida (duck typing tipado), sin depender de la
implementación concreta `pyteg.server.juego.mapa.Mapa`.
"""

from __future__ import annotations

from typing import Protocol


class MapaCalculos(Protocol):
    """Interfaz mínima del mapa requerida por `Calculos`."""

    def cantidad_de_paises_del_jugador(self, jugador: str) -> int:
        """Devuelve la cantidad de países que controla el jugador."""
        ...

    def jugador_controla_continente(self, jugador: str, continente: str) -> bool:
        """Indica si el jugador controla todos los países del continente."""
        ...
