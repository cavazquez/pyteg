from src.read_toml import ReadToml


def build_mapa(path):
    reader = ReadToml(path)
    mapa = {
        pais: [1, reader.continente(pais), None] for pais in reader.todos_los_paises()
    }
    return mapa
