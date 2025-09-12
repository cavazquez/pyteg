from pathlib import Path

from src.toml_reader import TomlReader


def build_mapa(path):  # noqa: ARG001
    # Para compatibilidad, asumimos que path es el directorio del tema
    paises_path = Path("themes/classic/paises.toml")
    cartas_path = Path("themes/classic/cartas.toml")
    adyacencias_path = Path("themes/classic/adyacencias.toml")
    paises_content = paises_path.read_text(encoding="utf-8")
    cartas_content = cartas_path.read_text(encoding="utf-8")
    adyacencias_content = adyacencias_path.read_text(encoding="utf-8")

    reader = TomlReader(paises_content, cartas_content, adyacencias_content)
    return {
        pais: [1, reader.continente(pais), None] for pais in reader.todos_los_paises()
    }
