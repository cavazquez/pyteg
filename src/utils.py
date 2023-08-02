from src.toml_reader import TomlReader


def build_mapa(path):
    reader = TomlReader(path)
    mapa = {
        pais: [1, reader.continente(pais), None] for pais in reader.todos_los_paises()
    }
    return mapa
