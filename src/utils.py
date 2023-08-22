from src.toml_reader import TomlReader


def build_mapa(path):
    reader = TomlReader(path)
    return {
        pais: [1, reader.continente(pais), None] for pais in reader.todos_los_paises()
    }
