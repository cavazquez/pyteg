"""Ajuste automático de posiciones para reducir solapamiento visible."""

from __future__ import annotations

import math
import re
from pathlib import Path

from PySide6.QtGui import QImage

from pyteg.gui.mapa.overlap_check import (
    PaisBounds,
    find_pixel_overlaps,
)
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

_EPS = 1e-6


def _center(bounds: PaisBounds) -> tuple[float, float]:
    return bounds.left + bounds.width / 2, bounds.top + bounds.height / 2


def _rebuild_bounds(
    reader: TomlReader,
    positions: dict[str, list[int]],
    *,
    folder: str = "themes/",
) -> list[PaisBounds]:
    bounds: list[PaisBounds] = []
    z_index = 0
    for continente in reader.get_continentes():
        cor_x, cor_y = reader.coordenadas_continente(continente)
        for pais in reader.get_paises(continente):
            pos_x, pos_y = positions[pais]
            image_path = Path(get_resource_path(folder + reader.img_path(pais)))
            image = QImage(str(image_path))
            bounds.append(
                PaisBounds(
                    name=pais,
                    continent=continente,
                    left=cor_x + pos_x,
                    top=cor_y + pos_y,
                    width=image.width(),
                    height=image.height(),
                    z_index=z_index,
                    image_path=image_path,
                )
            )
            z_index += 1
    return bounds


def compute_nudged_positions(  # noqa: PLR0914
    theme: str,
    *,
    step: float = 1.0,
    iterations: int = 4,
    min_pixels: int = 200,
    same_continent_only: bool = True,
) -> dict[str, tuple[int, int]]:
    """Empuja pares superpuestos en direcciones opuestas (mitad del paso cada uno).

    Returns:
        Posiciones finales ``pais -> (pos_x, pos_y)`` relativas al continente.

    """
    reader = TomlReader.from_theme(theme, strict=True)
    positions: dict[str, list[int]] = {}
    for continente in reader.get_continentes():
        for pais in reader.get_paises(continente):
            pos_x, pos_y, _, _ = reader.coordenadas(pais)
            positions[pais] = [pos_x, pos_y]

    half = step / 2
    for _ in range(iterations):
        bounds = _rebuild_bounds(reader, positions)
        overlaps = find_pixel_overlaps(bounds, min_pixels=min_pixels)
        for overlap in overlaps:
            if (
                same_continent_only
                and overlap.top.continent != overlap.bottom.continent
            ):
                continue
            top_name = overlap.top.name
            bottom_name = overlap.bottom.name
            tcx, tcy = _center(overlap.top)
            bcx, bcy = _center(overlap.bottom)
            dx = tcx - bcx
            dy = tcy - bcy
            length = math.hypot(dx, dy)
            if length < _EPS:
                dx, dy, length = 1.0, 0.0, 1.0
            nx = dx / length
            ny = dy / length
            positions[top_name][0] += round(half * nx)
            positions[top_name][1] += round(half * ny)
            positions[bottom_name][0] -= round(half * nx)
            positions[bottom_name][1] -= round(half * ny)

    return {name: (coords[0], coords[1]) for name, coords in positions.items()}


def apply_positions_to_paises_toml(
    theme: str, positions: dict[str, tuple[int, int]]
) -> Path:
    """Actualiza ``pos_x``/``pos_y`` en ``themes/{theme}/paises.toml``.

    Returns:
        Ruta al archivo modificado.

    """
    path = Path(get_resource_path(f"themes/{theme}/paises.toml"))
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    current_pais: str | None = None
    result: list[str] = []

    section_re = re.compile(r"^\[([A-Za-z]+)\.([A-Za-z]+)\]")
    pos_x_re = re.compile(r"^(\s*pos_x\s*=\s*)(-?\d+)")
    pos_y_re = re.compile(r"^(\s*pos_y\s*=\s*)(-?\d+)")

    for line in lines:
        match = section_re.match(line.strip())
        if match:
            current_pais = match.group(2)
            result.append(line)
            continue

        if current_pais and current_pais in positions:
            new_x, new_y = positions[current_pais]
            x_match = pos_x_re.match(line)
            if x_match:
                result.append(f"{x_match.group(1)}{new_x}\n")
                continue
            y_match = pos_y_re.match(line)
            if y_match:
                result.append(f"{y_match.group(1)}{new_y}\n")
                continue

        result.append(line)

    path.write_text("".join(result), encoding="utf-8")
    return path


def spread_continent_offsets(theme: str, *, gap: int = 8) -> dict[str, tuple[int, int]]:
    """Separa ligeramente los bloques de continente en el mapa mundial.

    Returns:
        Offsets finales ``continente -> (pos_x, pos_y)``.

    """
    reader = TomlReader.from_theme(theme, strict=True)
    continents = reader.get_continentes()
    offsets = {name: list(reader.coordenadas_continente(name)) for name in continents}

    min_continents = 2
    if len(continents) < min_continents:
        return {name: (coords[0], coords[1]) for name, coords in offsets.items()}

    cx = sum(offsets[name][0] for name in continents) / len(continents)
    cy = sum(offsets[name][1] for name in continents) / len(continents)

    for name in continents:
        ox, oy = offsets[name]
        dx = ox - cx
        dy = oy - cy
        length = math.hypot(dx, dy)
        if length < _EPS:
            continue
        offsets[name][0] = round(ox + gap * dx / length)
        offsets[name][1] = round(oy + gap * dy / length)

    return {name: (coords[0], coords[1]) for name, coords in offsets.items()}


def apply_continent_offsets_to_paises_toml(  # noqa: PLR0914
    theme: str, offsets: dict[str, tuple[int, int]]
) -> Path:
    """Actualiza ``pos_x``/``pos_y`` de secciones de continente en el TOML.

    Returns:
        Ruta al archivo modificado.

    """
    path = Path(get_resource_path(f"themes/{theme}/paises.toml"))
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    current_continent: str | None = None
    in_country_section = False
    result: list[str] = []

    continent_re = re.compile(r"^\[([A-Za-z]+)\]$")
    country_re = re.compile(r"^\[([A-Za-z]+)\.([A-Za-z]+)\]")
    pos_x_re = re.compile(r"^(\s*pos_x\s*=\s*)(-?\d+)")
    pos_y_re = re.compile(r"^(\s*pos_y\s*=\s*)(-?\d+)")

    for line in lines:
        stripped = line.strip()
        country_match = country_re.match(stripped)
        if country_match:
            in_country_section = True
            current_continent = None
            result.append(line)
            continue

        continent_match = continent_re.match(stripped)
        if continent_match:
            current_continent = continent_match.group(1)
            in_country_section = False
            result.append(line)
            continue

        if (
            current_continent
            and not in_country_section
            and current_continent in offsets
        ):
            new_x, new_y = offsets[current_continent]
            x_match = pos_x_re.match(line)
            if x_match:
                result.append(f"{x_match.group(1)}{new_x}\n")
                continue
            y_match = pos_y_re.match(line)
            if y_match:
                result.append(f"{y_match.group(1)}{new_y}\n")
                continue

        result.append(line)

    path.write_text("".join(result), encoding="utf-8")
    return path
