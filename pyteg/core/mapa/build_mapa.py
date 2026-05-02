"""Módulo para construir la estructura del mapa del juego."""

from __future__ import annotations

from typing import Any

from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path


def build_mapa() -> dict[str, list[Any]]:
    """Construye la estructura del mapa del juego desde archivos TOML.

    Returns:
        Diccionario con la estructura del mapa, donde cada clave es un país
        y el valor es una lista con [unidades, continente, dueño, [adyacentes]].

    """
    # Crear el lector TOML con archivos separados
    paises_path = get_resource_path("themes/classic/paises.toml")
    cartas_path = get_resource_path("themes/classic/cartas.toml")
    adyacencias_path = get_resource_path("themes/classic/adyacencias.toml")
    objetivos_path = get_resource_path("themes/classic/objetivos_secretos.toml")

    paises_content = paises_path.read_text(encoding="utf-8")
    cartas_content = cartas_path.read_text(encoding="utf-8")
    adyacencias_content = adyacencias_path.read_text(encoding="utf-8")
    objetivos_content = objetivos_path.read_text(encoding="utf-8")

    reader = TomlReader(
        paises_content, cartas_content, adyacencias_content, objetivos_content
    )

    # Construir el diccionario del mapa
    # Ahora cada país tendrá: [unidades, continente, dueño, [paises_adyacentes]]
    mapa: dict[str, list[Any]] = {}
    paises = reader.todos_los_paises()

    # Primero creamos todos los países con su información básica
    for pais in paises:
        continente = reader.continente(pais)
        # Inicializamos con unidades=1, continente, dueño=None, paises_adyacentes=[]
        mapa[pais] = [1, continente, None, []]

    # Luego agregamos las adyacencias a cada país
    for pais in paises:
        # Obtenemos los países adyacentes del lector TOML
        adyacentes = reader.obtener_paises_adyacentes(pais)
        # Aseguramos que el país exista en el mapa antes de agregar adyacencias
        if pais in mapa:
            mapa[pais][3] = adyacentes

    return mapa
