"""Módulo para construir la estructura del mapa del juego."""

from __future__ import annotations

from typing import Any

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.toml_reader import TomlReader


def build_mapa_from_reader(reader: TomlReader) -> dict[str, list[Any]]:
    """Construye el mapa a partir de un TomlReader ya cargado.

    Returns:
        Diccionario país → [unidades, continente, dueño, adyacentes].

    """
    mapa: dict[str, list[Any]] = {}
    paises = reader.todos_los_paises()

    for pais in paises:
        continente = reader.continente(pais)
        mapa[pais] = [1, continente, None, []]

    for pais in paises:
        adyacentes = reader.obtener_paises_adyacentes(pais)
        if pais in mapa:
            mapa[pais][3] = adyacentes

    return mapa


def build_mapa(theme: str = DEFAULT_MAP_THEME) -> dict[str, list[Any]]:
    """Construye la estructura del mapa del juego desde archivos TOML.

    Returns:
        Diccionario con la estructura del mapa, donde cada clave es un país
        y el valor es una lista con [unidades, continente, dueño, [adyacentes]].

    """
    reader = TomlReader.from_theme(theme, strict=True)
    return build_mapa_from_reader(reader)
