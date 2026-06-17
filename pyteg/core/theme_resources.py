"""Utilidades para resolver recursos de un tema de mapa."""

from __future__ import annotations

from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

_readers_cache: dict[tuple[str, bool], TomlReader] = {}


def get_theme_reader(theme: str, *, strict: bool = True) -> TomlReader:
    """Obtiene un TomlReader cacheado para el tema indicado.

    Returns:
        Instancia de TomlReader del tema.

    """
    key = (theme, strict)
    if key not in _readers_cache:
        _readers_cache[key] = TomlReader.from_theme(theme, strict=strict)
    return _readers_cache[key]


def get_card_image_path(theme: str, simbolo: str) -> str | None:
    """Resuelve la ruta absoluta de la imagen de una carta.

    Returns:
        Ruta absoluta al asset o None si el símbolo no está definido.

    """
    cartas = get_theme_reader(theme, strict=True).get_cartas()
    rel = cartas.get(simbolo)
    if rel is None:
        return None
    return str(get_resource_path(f"themes/{rel}"))
