"""
Información de versión del proyecto PyTeg.

Este módulo proporciona acceso a la versión del proyecto tanto desde
el archivo pyproject.toml como desde variables de entorno en tiempo
de compilación.
"""

import importlib
import os
from pathlib import Path


def _get_toml_loader():
    try:
        return importlib.import_module("tomllib")
    except ModuleNotFoundError:
        return importlib.import_module("tomli")


_toml_loader = _get_toml_loader()


def get_version() -> str:
    """
    Obtiene la versión del proyecto.

    Intenta obtener la versión desde:
    1. Variable de entorno PYTEG_VERSION (para binarios compilados)
    2. Archivo pyproject.toml (para desarrollo)
    3. Fallback a "unknown" si no se puede determinar

    Returns:
        str: Versión del proyecto (ej: "0.0.6")
    """
    # Primero intentar desde variable de entorno (para binarios)
    version = os.getenv("PYTEG_VERSION")
    if version:
        return version

    # Intentar leer desde pyproject.toml (para desarrollo)
    try:
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                data = _toml_loader.load(f)
                return data.get("project", {}).get("version", "unknown")
    except (OSError, ValueError, KeyError):
        # Error al leer archivo o parsear TOML
        pass

    return "unknown"


def get_version_info() -> dict[str, str]:
    """
    Obtiene información completa de versión.

    Returns:
        dict: Diccionario con información de versión
    """
    version = get_version()
    return {
        "version": version,
        "name": "PyTeg",
        "description": "Juego de estrategia TEG implementado en Python",
    }


# Constantes para uso directo
VERSION = get_version()
NAME = "PyTeg"
DESCRIPTION = "Juego de estrategia TEG implementado en Python"

if __name__ == "__main__":
    # Mostrar información de versión cuando se ejecuta directamente
    info = get_version_info()
    print(f"{info['name']} v{info['version']}")
    print(info["description"])
