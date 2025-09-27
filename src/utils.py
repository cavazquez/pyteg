from pathlib import Path

from src.toml_reader import TomlReader

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Obtiene la ruta absoluta a un recurso del proyecto.

    Esta función garantiza que los recursos se encuentren tanto en desarrollo
    como en binarios empaquetados con Nuitka.

    Args:
        relative_path: Ruta relativa desde el directorio raíz del proyecto

    Returns:
        Path: Ruta absoluta al recurso

    Example:
        >>> get_resource_path("icons/conectar.png")
        PosixPath('/path/to/project/icons/conectar.png')
    """
    return BASE_DIR / relative_path


def build_mapa(path):  # noqa: ARG001
    # Para compatibilidad, asumimos que path es el directorio del tema
    paises_path = get_resource_path("themes/classic/paises.toml")
    cartas_path = get_resource_path("themes/classic/cartas.toml")
    adyacencias_path = get_resource_path("themes/classic/adyacencias.toml")
    paises_content = paises_path.read_text(encoding="utf-8")
    cartas_content = cartas_path.read_text(encoding="utf-8")
    adyacencias_content = adyacencias_path.read_text(encoding="utf-8")

    reader = TomlReader(paises_content, cartas_content, adyacencias_content)
    return {
        pais: [1, reader.continente(pais), None] for pais in reader.todos_los_paises()
    }
