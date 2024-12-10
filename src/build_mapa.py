from pathlib import Path

from src.toml_reader import TomlReader


def build_mapa():
    reader = TomlReader(
        Path("themes/test/paises.toml").read_text(encoding="locale"),
    )
    mapa = {}

    paises = reader.todos_los_paises()
    for pais in paises:
        continente = reader.continente(pais)
        mapa.update({pais: [1, continente, None]})

    return mapa
