"""Información de versión del proyecto PyTeg.

Este módulo proporciona acceso a la versión del proyecto tanto desde
el archivo pyproject.toml como desde variables de entorno en tiempo
de compilación.
"""

from __future__ import annotations

import importlib
import os
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def _get_toml_loader() -> ModuleType:
    try:
        return importlib.import_module("tomllib")
    except ModuleNotFoundError:
        return importlib.import_module("tomli")


_toml_loader = _get_toml_loader()


def _get_version_from_pyproject() -> str | None:
    """Lee la versión del archivo de proyecto si está disponible.

    Returns:
        Versión declarada o ``None`` cuando no se puede leer.

    """
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    try:
        with pyproject_path.open("rb") as file:
            data = _toml_loader.load(file)
    except OSError, ValueError, KeyError:
        return None
    version = data.get("project", {}).get("version")
    return version if isinstance(version, str) else None


def get_version() -> str:
    """Obtiene la versión del proyecto.

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
    version = _get_version_from_pyproject()
    if version is not None:
        return version

    # En un wheel instalado no se distribuye pyproject.toml. En ese caso, usar
    # la metadata estándar del paquete para conservar la versión visible en
    # los entry points y en los logs.
    try:
        return metadata.version("pyteg")
    except metadata.PackageNotFoundError:
        pass

    return "unknown"


def get_version_info() -> dict[str, str]:
    """Obtiene información completa de versión.

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
