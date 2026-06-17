"""Dataclasses de layout del mapa definidas en TOML (no estado de partida)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeCountryLayout:
    """Layout gráfico y de archivo de un país en un tema."""

    nombre: str
    continente: str
    file: str
    pos_x: int
    pos_y: int
    army_x: int
    army_y: int


@dataclass(frozen=True)
class ThemeContinentLayout:
    """Layout de un continente y sus países en un tema."""

    nombre: str
    pos_x: int
    pos_y: int
    paises: dict[str, ThemeCountryLayout]
