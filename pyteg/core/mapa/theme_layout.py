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


@dataclass(frozen=True)
class ThemeVisualConnection:
    """Conexión visual opcional entre dos países de un tema.

    ``puntos`` contiene puntos intermedios en coordenadas absolutas de la
    escena. Los extremos se calculan desde el centro de cada imagen para que
    un cambio de tamaño del asset no obligue a actualizar el TOML.
    """

    origen: str
    destino: str
    puntos: tuple[tuple[float, float], ...] = ()
