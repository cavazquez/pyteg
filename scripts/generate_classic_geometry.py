"""Generate the classic map's SVG layers from shared landmass partitions.

Each ``*-partition.png`` stores one byte per pixel: zero is water and labels
1..N correspond to the manifest's ``country_order``. A companion block mask
describes the same landmass independently. The generator rejects any mismatch
between the union of countries and that block before writing an SVG.

Run ``python -m scripts.generate_classic_geometry`` to update generated files,
or add ``--check`` to verify that they are current without changing them.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any, cast
from xml.sax.saxutils import escape

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
MAX_LABEL = 255
COORDINATE_COUNT = 2
BOUND_COUNT = 4

type Point = tuple[int, int]
type Edges = dict[Point, list[Point]]


def _number(value: float) -> str:
    return f"{value:g}"


def _pixel_data(path: Path) -> tuple[int, int, bytes]:
    image = QImage(str(path))
    if image.isNull():
        msg = f"No se pudo leer la máscara: {path}"
        raise ValueError(msg)
    image = image.convertToFormat(QImage.Format.Format_Grayscale8)
    width, height = image.width(), image.height()
    stride = image.bytesPerLine()
    bits = image.constBits()
    pixels = b"".join(
        bytes(bits[row * stride : row * stride + width]) for row in range(height)
    )
    return width, height, pixels


def _add_edge(edges: Edges, start: Point, end: Point) -> None:
    edges[start].append(end)


def _outlines(  # noqa: C901
    labels: bytes, width: int, height: int, count: int
) -> tuple[list[Edges], Edges]:
    """Trace directed pixel-grid edges for countries and their shared shell.

    Returns:
        Directed edges for each country label and for the full landmass.

    """
    countries: list[Edges] = [defaultdict(list) for _ in range(count + 1)]
    shell: Edges = defaultdict(list)
    for y in range(height):
        row = y * width
        for x in range(width):
            label = labels[row + x]
            if not label:
                continue
            top = labels[row - width + x] if y else 0
            right = labels[row + x + 1] if x + 1 < width else 0
            bottom = labels[row + width + x] if y + 1 < height else 0
            left = labels[row + x - 1] if x else 0
            if top != label:
                _add_edge(countries[label], (x, y), (x + 1, y))
            if right != label:
                _add_edge(countries[label], (x + 1, y), (x + 1, y + 1))
            if bottom != label:
                _add_edge(countries[label], (x + 1, y + 1), (x, y + 1))
            if left != label:
                _add_edge(countries[label], (x, y + 1), (x, y))
            if not top:
                _add_edge(shell, (x, y), (x + 1, y))
            if not right:
                _add_edge(shell, (x + 1, y), (x + 1, y + 1))
            if not bottom:
                _add_edge(shell, (x + 1, y + 1), (x, y + 1))
            if not left:
                _add_edge(shell, (x, y + 1), (x, y))
    return countries, shell


_DIRECTION = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
_TURN_ORDER = {1: 0, 0: 1, 3: 2, 2: 3}


def _path_from_edges(  # noqa: C901
    edges: Edges, scale: int, origin: tuple[float, float]
) -> str:
    """Join grid edges into exact closed SVG contours (including holes).

    Returns:
        SVG path data for all contours in the edge collection.

    Raises:
        ValueError: If the mask produced an open or degenerate contour.

    """

    def svg_point(point: Point) -> str:
        return (
            f"{_number(origin[0] + point[0] / scale)} "
            f"{_number(origin[1] + point[1] / scale)}"
        )

    paths: list[str] = []
    while edges:
        start = next(iter(edges))
        current = edges[start].pop()
        if not edges[start]:
            del edges[start]
        loop = [start, current]
        while current != start:
            outgoing = edges.get(current)
            if not outgoing:
                msg = f"Contorno abierto en {current}"
                raise ValueError(msg)
            if len(outgoing) == 1:
                following = outgoing.pop()
            else:
                previous = loop[-2]
                direction = _DIRECTION[
                    current[0] - previous[0], current[1] - previous[1]
                ]
                following = min(
                    outgoing,
                    key=lambda point: _TURN_ORDER[
                        (
                            _DIRECTION[point[0] - current[0], point[1] - current[1]]
                            - direction
                        )
                        % 4
                    ],
                )
                outgoing.remove(following)
            if not outgoing:
                del edges[current]
            loop.append(following)
            current = following
        corners = [loop[0]]
        for index in range(1, len(loop) - 1):
            before, point, after = loop[index - 1 : index + 2]
            if (point[0] - before[0], point[1] - before[1]) != (
                after[0] - point[0],
                after[1] - point[1],
            ):
                corners.append(point)
        if len(corners) < BOUND_COUNT:
            msg = "El contorno tiene menos de cuatro vértices"
            raise ValueError(msg)
        paths.append("M " + " L ".join(map(svg_point, corners)) + " Z")
    return " ".join(paths)


def _internal_borders(  # noqa: C901
    labels: bytes, width: int, height: int, scale: int, origin: tuple[float, float]
) -> str:
    """Draw every edge between two different countries exactly once.

    Returns:
        SVG path data containing all internal divisions.

    """
    commands: list[str] = []

    def x_position(pixel: int) -> str:
        return _number(origin[0] + pixel / scale)

    def y_position(pixel: int) -> str:
        return _number(origin[1] + pixel / scale)

    for y in range(height - 1):
        x = 0
        while x < width:
            first = labels[y * width + x]
            second = labels[(y + 1) * width + x]
            if first and second and first != second:
                start = x
                x += 1
                while x < width:
                    above = labels[y * width + x]
                    below = labels[(y + 1) * width + x]
                    if not (above and below and above != below):
                        break
                    x += 1
                commands.append(
                    f"M {x_position(start)} {y_position(y + 1)} "
                    f"L {x_position(x)} {y_position(y + 1)}"
                )
            else:
                x += 1
    for x in range(width - 1):
        y = 0
        while y < height:
            first = labels[y * width + x]
            second = labels[y * width + x + 1]
            if first and second and first != second:
                start = y
                y += 1
                while y < height:
                    left = labels[y * width + x]
                    right = labels[y * width + x + 1]
                    if not (left and right and left != right):
                        break
                    y += 1
                commands.append(
                    f"M {x_position(x + 1)} {y_position(start)} "
                    f"L {x_position(x + 1)} {y_position(y)}"
                )
            else:
                y += 1
    return " ".join(commands)


def _country_files(theme_dir: Path) -> dict[str, Path]:
    data = tomllib.loads((theme_dir / "paises.toml").read_text(encoding="utf-8"))
    files: dict[str, Path] = {}
    for continent in data.values():
        if not isinstance(continent, dict):
            continue
        for name, details in continent.items():
            if not isinstance(details, dict) or "file" not in details:
                continue
            path = (theme_dir.parent / details["file"]).resolve()
            if not path.is_relative_to(theme_dir.resolve()):
                msg = f"Archivo de país fuera del tema clásico: {path}"
                raise ValueError(msg)
            files[name] = path
    return files


def _manifest_data(path: Path) -> dict[str, Any]:
    data = cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))
    required = {
        "origin",
        "size",
        "scale",
        "country_order",
        "country_bounds",
        "fill",
        "stroke",
    }
    missing = required - data.keys()
    if missing:
        msg = f"Manifest incompleto {path}: {', '.join(sorted(missing))}"
        raise ValueError(msg)
    return data


def _png_from_svg(svg: str, width: int, height: int) -> bytes:
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        msg = "No se pudo cargar un SVG de país generado"
        raise ValueError(msg)
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, on=True)
    renderer.render(painter)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):  # type: ignore[call-overload]
        msg = "No se pudo codificar un PNG de país generado"
        raise ValueError(msg)
    return bytes(buffer.data())


def _generate_one(  # noqa: C901, PLR0914, PLR0915
    manifest_path: Path, geometry_dir: Path, countries: dict[str, Path]
) -> dict[Path, bytes]:
    slug = manifest_path.name.removesuffix("-manifest.json")
    manifest = _manifest_data(manifest_path)
    names: list[str] = manifest["country_order"]
    if len(set(names)) != len(names) or not names:
        msg = f"Países duplicados o vacíos en {manifest_path}"
        raise ValueError(msg)
    if len(names) > MAX_LABEL or set(manifest["country_bounds"]) != set(names):
        msg = f"Límites o cantidad de países inválidos en {manifest_path}"
        raise ValueError(msg)
    unknown = set(names) - countries.keys()
    if unknown:
        msg = f"Países desconocidos en {manifest_path}: {', '.join(sorted(unknown))}"
        raise ValueError(msg)
    scale = int(manifest["scale"])
    if scale <= 0:
        msg = f"Escala inválida en {manifest_path}"
        raise ValueError(msg)
    raw_origin = manifest["origin"]
    raw_size = manifest["size"]
    if len(raw_origin) != COORDINATE_COUNT or len(raw_size) != COORDINATE_COUNT:
        msg = f"Origen o tamaño inválido en {manifest_path}"
        raise ValueError(msg)
    origin = (float(raw_origin[0]), float(raw_origin[1]))
    size = (float(raw_size[0]), float(raw_size[1]))
    width, height, labels = _pixel_data(geometry_dir / f"{slug}-partition.png")
    shell_width, shell_height, shell = _pixel_data(geometry_dir / f"{slug}-block.png")
    if (width, height) != (shell_width, shell_height) or (width, height) != (
        round(size[0] * scale),
        round(size[1] * scale),
    ):
        msg = f"Tamaños incompatibles de partición y bloque en {manifest_path}"
        raise ValueError(msg)
    if set(labels) != set(range(len(names) + 1)):
        msg = f"Etiquetas fuera de 0..N en {manifest_path}"
        raise ValueError(msg)
    if set(shell) - {0, MAX_LABEL} or any(
        (label != 0) != (land == MAX_LABEL)
        for label, land in zip(labels, shell, strict=True)
    ):
        msg = f"La unión de los países no coincide con el bloque en {manifest_path}"
        raise ValueError(msg)

    country_edges, shell_edges = _outlines(labels, width, height, len(names))
    shell_path = _path_from_edges(shell_edges, scale, (0.0, 0.0))
    country_paths = {
        name: _path_from_edges(country_edges[index], scale, origin)
        for index, name in enumerate(names, start=1)
    }
    border_path = _internal_borders(labels, width, height, scale, (0.0, 0.0))
    fill = escape(str(manifest["fill"]), {'"': "&quot;"})
    stroke = escape(str(manifest["stroke"]), {'"': "&quot;"})
    origin_x, origin_y = map(_number, origin)
    scene_width, scene_height = map(_number, size)
    svg_open_local = (
        f'<svg xmlns="{SVG_NS}" width="{scene_width}" height="{scene_height}" '
        f'viewBox="0 0 {scene_width} {scene_height}">'
    )
    svg_open_scene = (
        f'<svg xmlns="{SVG_NS}" width="{scene_width}" height="{scene_height}" '
        f'viewBox="{origin_x} {origin_y} {scene_width} {scene_height}">'
    )
    coastline = (
        f'<path id="landmass-{slug}" d="{shell_path}" '
        f'fill="none" stroke="{stroke}" '
        'stroke-width="1" vector-effect="non-scaling-stroke"/>'
    )
    divisions = (
        f'<path id="internal-borders" d="{border_path}" fill="none" '
        f'stroke="{stroke}" stroke-width="1" '
        'vector-effect="non-scaling-stroke"/>'
    )
    outputs: dict[Path, str | bytes] = {
        geometry_dir / f"{slug}-shell.svg": (
            svg_open_local
            + f'<path d="{shell_path}" fill="{fill}" fill-rule="evenodd"/>'
            + "</svg>\n"
        ),
        geometry_dir / f"{slug}-borders.svg": (
            svg_open_local + coastline + divisions + "</svg>\n"
        ),
    }
    country_elements: list[str] = []
    for name in names:
        bounds = manifest["country_bounds"][name]
        if len(bounds) != BOUND_COUNT or bounds[2] <= 0 or bounds[3] <= 0:
            msg = f"Límites inválidos de {name} en {manifest_path}"
            raise ValueError(msg)
        x, y, country_width, country_height = map(_number, bounds)
        country_elements.append(
            f'<path id="{escape(name)}" '
            f'data-bounds="{x} {y} {country_width} {country_height}" '
            f'd="{country_paths[name]}" fill="{fill}" fill-rule="evenodd"/>'
        )
        country_svg = (
            f'<svg xmlns="{SVG_NS}" width="{country_width}" '
            f'height="{country_height}" '
            f'viewBox="{x} {y} {country_width} {country_height}">'
            f'<path d="{country_paths[name]}" fill="{fill}" fill-rule="evenodd"/>'
            "</svg>\n"
        )
        outputs[countries[name]] = country_svg
        outputs[countries[name].with_suffix(".png")] = _png_from_svg(
            country_svg, int(bounds[2]), int(bounds[3])
        )
    outputs[geometry_dir / f"{slug}-canonical.svg"] = (
        svg_open_scene
        + '<g id="countries">'
        + "".join(country_elements)
        + "</g>"
        + f'<g transform="translate({origin_x} {origin_y})">'
        + coastline
        + divisions
        + "</g></svg>\n"
    )
    return {
        path: content.encode("utf-8") if isinstance(content, str) else content
        for path, content in outputs.items()
    }


def generate(theme_dir: Path, geometry_dir: Path, *, check: bool) -> int:
    """Write or verify SVG and PNG assets for all available classic landmasses.

    Returns:
        Zero if all files are current or updated, otherwise one.

    Raises:
        ValueError: If an input manifest or generated path is invalid.

    """
    countries = _country_files(theme_dir)
    manifests = sorted(geometry_dir.glob("*-manifest.json"))
    if not manifests:
        msg = f"No hay manifests de geometría en {geometry_dir}"
        raise ValueError(msg)
    generated: dict[Path, bytes] = {}
    seen_countries: set[Path] = set()
    for manifest in manifests:
        outputs = _generate_one(manifest, geometry_dir, countries)
        for path, content in outputs.items():
            if path in generated:
                msg = f"SVG generado dos veces: {path}"
                raise ValueError(msg)
            generated[path] = content
            if path.parent == theme_dir and path.suffix == ".svg":
                seen_countries.add(path)

    outdated = [
        path
        for path, content in generated.items()
        if not path.is_file() or path.read_bytes() != content
    ]
    if check:
        for path in outdated:
            print(f"Desactualizado: {path.relative_to(theme_dir.parent)}")
        if outdated:
            return 1
        print(
            f"Geometría clásica al día: {len(manifests)} bloques, "
            f"{len(seen_countries)} países"
        )
        return 0
    for path in outdated:
        path.write_bytes(generated[path])
    print(
        f"Geometría clásica generada: {len(manifests)} bloques, "
        f"{len(seen_countries)} países, {len(outdated)} archivos actualizados"
    )
    return 0


def main() -> int:
    """Parse CLI arguments.

    Returns:
        Process exit status.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Compara sin escribir archivos"
    )
    parser.add_argument(
        "--theme-dir",
        type=Path,
        default=REPO_ROOT / "themes" / "classic",
        help="Directorio del tema clásico",
    )
    parser.add_argument(
        "--geometry-dir",
        type=Path,
        help="Directorio de máscaras, manifests y SVG generados",
    )
    args = parser.parse_args()
    theme_dir = args.theme_dir.resolve()
    geometry_dir = (args.geometry_dir or theme_dir / "geometry").resolve()
    try:
        return generate(theme_dir, geometry_dir, check=args.check)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
