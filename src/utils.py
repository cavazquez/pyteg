"""Utilidades generales del proyecto PyTeg."""

from __future__ import annotations

from pathlib import Path

from src.toml_reader import TomlReader

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta a un recurso del proyecto."""
    return BASE_DIR / relative_path


def build_mapa(path: Path | str) -> dict[str, list[object]]:  # noqa: ARG001
    """Construye un mapa compatible con las expectativas del servidor."""
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
