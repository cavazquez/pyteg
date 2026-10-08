# ruff: noqa: D103, DOC201, DOC501, E501, EM101, EM102, INP001, PLR2004, TRY003
"""Genera los SVG de Revancha a partir de contornos editables del tablero.

board-layout.toml contiene los contornos, etiquetas y marcadores trazados sobre
la referencia frontal de 800 x 600. Una partición común conserva los huecos y
las islas sin solapar las superficies de clic; el grafo TOML sigue definiendo
las acciones permitidas. Las rutas de agua se declaran para toda arista cuyos
contornos no se tocan, incluyendo las islas dentro de un mismo continente.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QByteArray, QRect, QRectF, Qt
from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QGuiApplication,
    QImage,
    QPainter,
    QPainterPath,
    QRegion,
    QTransform,
)
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[3]
THEME = ROOT / "themes" / "revancha"
SCALE = 1.25
WIDTH = 1000
HEIGHT = 750
MARGIN = 3.0
BOARD = tomllib.loads(
    (THEME / "geometry" / "board-layout.toml").read_text(encoding="utf-8")
)["Paises"]
CENTERS = {name: tuple(country["marcador"]) for name, country in BOARD.items()}
CONTINENTS = {
    "AmericaDelNorte": {"fill": "#cc7663", "edge": "#ab4f48"},
    "AmericaCentral": {"fill": "#dec373", "edge": "#b18c41"},
    "AmericaDelSur": {"fill": "#c45662", "edge": "#963d4c"},
    "Europa": {"fill": "#c16ba9", "edge": "#a1478c"},
    "Africa": {"fill": "#d97b71", "edge": "#b65356"},
    "Asia": {"fill": "#c4bd77", "edge": "#989052"},
    "Oceania": {"fill": "#83bcb0", "edge": "#56998b"},
}
DISPLAY_NAMES = {
    "LasVegas": "LAS VEGAS",
    "NuevaYork": "NUEVA YORK",
    "IslaVictoria": "ISLA VICTORIA",
    "GranBretana": "GRAN BRETAÑA",
    "NuevaZelandia": "NUEVA ZELANDIA",
    "ElSalvador": "EL SALVADOR",
    "Canada": "CANADÁ",
    "Oregon": "OREGÓN",
    "Mexico": "MÉXICO",
    "Espana": "ESPAÑA",
    "Sudafrica": "SUDÁFRICA",
    "Etiopia": "ETIOPÍA",
    "Iran": "IRÁN",
    "Turquia": "TURQUÍA",
    "Japon": "JAPÓN",
}
# Long bridges follow the same open ocean corridors as the reference board.
CONNECTIONS = [
    ("Alaska", "Chukchi", [(217, 49), (337, 30), (473, 30), (534, 79)]),
    ("Alaska", "Kamchatka", [(194, 40), (335, 22), (469, 22), (749, 49), (748, 134)]),
    ("Groenlandia", "Islandia", [(320, 128)]),
    ("California", "Tonga", [(0, 251), (800, 396)], "horizontal"),
    ("Brasil", "Sahara", [(309, 433)]),
    ("Uruguay", "Nigeria", [(326, 476)]),
    ("Espana", "Sahara", [(377, 336)]),
    ("Polonia", "Egipto", [(505, 292), (492, 344)]),
    ("Chile", "Australia", [(0, 494), (800, 480)], "horizontal"),
    ("India", "Sumatra", [(640, 375)]),
    ("Filipinas", "Australia", [(715, 437)]),
]
continent_for: dict[str, str] = {}
marker_positions: dict[str, tuple[int, int]] = {}
LABEL_FONT = "DejaVu Sans"
LABEL_INK = "#282a30"
LABEL_HALO = "#fff8ea"
label_reservations: list[int] = []


def label_geometry(name: str) -> tuple[QPainterPath, str, float, float, float, float]:
    """Reserve the rotated text box, including its halo and clearance."""
    layout = BOARD[name]
    x, y = scene_point(layout["etiqueta"])
    angle = layout.get("angulo", 0)
    text = DISPLAY_NAMES.get(name, name).title()
    size = layout.get("tamano", 12)
    font = QFont(LABEL_FONT)
    font.setPixelSize(size)
    font.setWeight(QFont.Weight.DemiBold)
    metrics = QFontMetricsF(font)
    glyphs = QPainterPath()
    glyphs.addText(-metrics.horizontalAdvance(text) / 2, 0, font, text)
    rect = glyphs.boundingRect()
    path = QPainterPath()
    path.addRect(rect.adjusted(-2, -2, 2, 2))
    transform = QTransform().translate(x, y).rotate(angle)
    return transform.map(path), text, x, y, angle, size


def label_glyphs(name: str) -> QPainterPath:
    """Bake glyphs into vector paths so installed fonts cannot alter the layout."""
    _reservation, text, x, y, angle, size = label_geometry(name)
    font = QFont(LABEL_FONT)
    font.setPixelSize(int(size))
    font.setWeight(QFont.Weight.DemiBold)
    path = QPainterPath()
    path.addText(-QFontMetricsF(font).horizontalAdvance(text) / 2, 0, font, text)
    return QTransform().translate(x, y).rotate(angle).map(path)


def painter_svg_path(path: QPainterPath) -> str:
    commands = []
    index = 0
    while index < path.elementCount():
        element = path.elementAt(index)
        if element.isMoveTo():
            commands.append(f"M {fmt(element.x)} {fmt(element.y)}")
        elif element.isLineTo():
            commands.append(f"L {fmt(element.x)} {fmt(element.y)}")
        else:
            control = path.elementAt(index + 1)
            end = path.elementAt(index + 2)
            commands.append(
                f"C {fmt(element.x)} {fmt(element.y)} {fmt(control.x)} {fmt(control.y)} {fmt(end.x)} {fmt(end.y)}"
            )
            index += 2
        index += 1
    return " ".join(commands)


def _reserve_labels() -> None:
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGBA8888)
    image.fill(0)
    painter = QPainter(image)
    for name in BOARD:
        painter.fillPath(label_geometry(name)[0], Qt.GlobalColor.white)
    painter.end()
    pixels = image.constBits()
    stride = WIDTH + 1
    label_reservations.clear()
    label_reservations.extend([0] * (stride * (HEIGHT + 1)))
    for y in range(HEIGHT):
        running = 0
        for x in range(WIDTH):
            running += pixels[(y * WIDTH + x) * 4 + 3] > 0
            label_reservations[(y + 1) * stride + x + 1] = (
                label_reservations[y * stride + x + 1] + running
            )


def _reserved_pixels(x: int, y: int) -> int:
    stride = WIDTH + 1
    x0, y0 = max(0, x - 1), max(0, y - 1)
    x1, y1 = min(WIDTH, x + 17), min(HEIGHT, y + 17)
    return (
        label_reservations[y1 * stride + x1]
        - label_reservations[y0 * stride + x1]
        - label_reservations[y1 * stride + x0]
        + label_reservations[y0 * stride + x0]
    )


def scene_point(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] * SCALE, point[1] * SCALE


def fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def svg_path(points: list[tuple[float, float]]) -> str:
    return "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in points) + " Z"


def curved_contour(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Bend each shared edge identically in either traversal direction."""
    result = []
    for start, end in zip(points, points[1:] + points[:1], strict=True):
        first, second = sorted((start, end))
        dx, dy = second[0] - first[0], second[1] - first[1]
        length = math.hypot(dx, dy) or 1
        digest = hashlib.sha256(f"{first}:{second}".encode()).digest()
        bend = (digest[0] / 255 * 2 - 1) * min(2.0, length * 0.10)
        control = (
            (first[0] + second[0]) / 2 - dy / length * bend,
            (first[1] + second[1]) / 2 + dx / length * bend,
        )
        result.append(start)
        for sample in range(1, 5):
            t = sample / 5
            result.append((
                (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t * t * end[0],
                (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t * t * end[1],
            ))
    return result


def lighten(color: str, fraction: float) -> str:
    channels = [int(color[index : index + 2], 16) for index in (1, 3, 5)]
    return "#" + "".join(
        f"{round(channel + (255 - channel) * fraction):02x}" for channel in channels
    )


def make_country_mask(name: str) -> tuple[str, tuple[int, int, int, int]]:
    points = [
        scene_point(point)
        for point in curved_contour([tuple(point) for point in BOARD[name]["contorno"]])
    ]
    left, top = (
        math.floor(min(x for x, _ in points) - MARGIN),
        math.floor(min(y for _, y in points) - MARGIN),
    )
    right, bottom = (
        math.ceil(max(x for x, _ in points) + MARGIN),
        math.ceil(max(y for _, y in points) + MARGIN),
    )
    width, height = right - left, bottom - top
    path = svg_path([(x - left, y - top) for x, y in points])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><path d="{path}" fill="#ffffff"/></svg>',
        (left, top, width, height),
    )


def _render_country_mask(svg: str, width: int, height: int) -> QImage:
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        raise ValueError("No se pudo renderizar un país de Revancha")
    image = QImage(width, height, QImage.Format.Format_RGBA8888)
    image.fill(0)
    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    return image


def _allowed_pairs() -> set[frozenset[str]]:
    data = tomllib.loads((THEME / "adyacencias.toml").read_text(encoding="utf-8"))
    return {
        frozenset((origin, destination))
        for origin, destinations in data["Adyacencias"].items()
        for destination in destinations
    }


def _country_partition(  # noqa: PLR0914
    base_assets: dict[str, tuple[str, tuple[int, int, int, int]]],
) -> tuple[bytearray, list[str]]:
    """Assign each opaque pixel to one country, including overlapping shells."""
    names = list(base_assets)
    label_for = {name: index for index, name in enumerate(names, start=1)}
    owners = bytearray(WIDTH * HEIGHT)
    seeds = {name: scene_point(CENTERS[name]) for name in names}
    for name, (svg, (left, top, width, height)) in base_assets.items():
        image = _render_country_mask(svg, width, height)
        pixels = image.constBits()
        stride = image.bytesPerLine()
        own_label = label_for[name]
        own_x, own_y = seeds[name]
        for local_y in range(height):
            scene_y = top + local_y
            if not 0 <= scene_y < HEIGHT:
                continue
            row = local_y * stride
            owner_row = scene_y * WIDTH
            for local_x in range(width):
                scene_x = left + local_x
                if not 0 <= scene_x < WIDTH or pixels[row + local_x * 4 + 3] < 128:
                    continue
                offset = owner_row + scene_x
                previous = owners[offset]
                if previous:
                    previous_x, previous_y = seeds[names[previous - 1]]
                    previous_distance = (scene_x - previous_x) ** 2 + (
                        scene_y - previous_y
                    ) ** 2
                    own_distance = (scene_x - own_x) ** 2 + (scene_y - own_y) ** 2
                    if previous_distance <= own_distance:
                        continue
                owners[offset] = own_label
    return owners, names


def _separate_forbidden_contacts(  # noqa: C901
    owners: bytearray, names: list[str]
) -> None:
    """Open a narrow water gap wherever nonadjacent territories meet."""
    allowed = _allowed_pairs()
    boundary: set[int] = set()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            offset = y * WIDTH + x
            label = owners[offset]
            if not label:
                continue
            for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                    continue
                neighbor_offset = ny * WIDTH + nx
                other = owners[neighbor_offset]
                if (
                    other
                    and other != label
                    and frozenset((names[label - 1], names[other - 1])) not in allowed
                ):
                    boundary.update((offset, neighbor_offset))

    # A second pixel on each side keeps the gap visible after fitInView.
    gap = set(boundary)
    for offset in boundary:
        x, y = offset % WIDTH, offset // WIDTH
        label = owners[offset]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    candidate = ny * WIDTH + nx
                    if owners[candidate] == label:
                        gap.add(candidate)
    for offset in gap:
        owners[offset] = 0


def _country_bounds(owners: bytearray, count: int) -> list[tuple[int, int, int, int]]:
    bounds = [[WIDTH, HEIGHT, -1, -1] for _ in range(count + 1)]
    for offset, label in enumerate(owners):
        if not label:
            continue
        x, y = offset % WIDTH, offset // WIDTH
        item = bounds[label]
        item[0] = min(item[0], x)
        item[1] = min(item[1], y)
        item[2] = max(item[2], x)
        item[3] = max(item[3], y)
    result = []
    for label in range(1, count + 1):
        left, top, right, bottom = bounds[label]
        if right < left or bottom < top:
            raise ValueError(f"El país {label} desapareció al separar fronteras")
        left = max(0, left - int(MARGIN))
        top = max(0, top - int(MARGIN))
        right = min(WIDTH, right + int(MARGIN) + 1)
        bottom = min(HEIGHT, bottom + int(MARGIN) + 1)
        result.append((left, top, right - left, bottom - top))
    return result


_DIRECTION = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
_TURN_ORDER = {1: 0, 0: 1, 3: 2, 2: 3}


def _outline_path(  # noqa: C901, PLR0912, PLR0914
    owners: bytearray, label: int, bounds: tuple[int, int, int, int]
) -> str:
    """Trace pixel-grid contours; holes and islands remain selectable."""
    left, top, width, height = bounds
    edges: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for y in range(top, top + height):
        for x in range(left, left + width):
            if owners[y * WIDTH + x] != label:
                continue
            if y == 0 or owners[(y - 1) * WIDTH + x] != label:
                edges[x, y].append((x + 1, y))
            if x + 1 == WIDTH or owners[y * WIDTH + x + 1] != label:
                edges[x + 1, y].append((x + 1, y + 1))
            if y + 1 == HEIGHT or owners[(y + 1) * WIDTH + x] != label:
                edges[x + 1, y + 1].append((x, y + 1))
            if x == 0 or owners[y * WIDTH + x - 1] != label:
                edges[x, y + 1].append((x, y))

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
                raise ValueError(f"Contorno abierto del país {label} en {current}")
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
        paths.append(
            "M " + " L ".join(f"{x - left} {y - top}" for x, y in corners) + " Z"
        )
    return " ".join(paths)


def _marker_position(  # noqa: C901, PLR0914
    owners: bytearray, label: int, bounds: tuple[int, int, int, int], name: str
) -> tuple[int, int]:
    """Find the best 16-pixel marker site inside its own country."""
    left, top, width, height = bounds
    stride = width + 1
    sums = [0] * (stride * (height + 1))
    candidates: list[tuple[int, int]] = []
    region = QRegion()
    for y in range(height):
        running = 0
        run_start = None
        for x in range(width):
            scene_x, scene_y = left + x, top + y
            is_own = owners[scene_y * WIDTH + scene_x] == label
            running += is_own
            sums[(y + 1) * stride + x + 1] = sums[y * stride + x + 1] + running
            if is_own:
                candidates.append((scene_x, scene_y))
                if run_start is None:
                    run_start = scene_x
            elif run_start is not None:
                region |= QRegion(QRect(run_start, scene_y, scene_x - run_start, 1))
                run_start = None
        if run_start is not None:
            region |= QRegion(QRect(run_start, top + y, left + width - run_start, 1))

    target_x, target_y = scene_point(CENTERS[name])
    country_shape = QPainterPath()
    country_shape.addRegion(region)
    country_shape = country_shape.simplified()
    candidates.sort(
        key=lambda point: (point[0] - target_x) ** 2 + (point[1] - target_y) ** 2
    )
    reservations = [
        label_geometry(country)[0]
        for country in BOARD
        if label_geometry(country)[0]
        .boundingRect()
        .intersects(QRectF(left, top, width, height))
    ]
    circle_pixels = [
        (dx, dy)
        for dy in range(-8, 8)
        for dx in range(-8, 8)
        if (dx + 0.5) ** 2 + (dy + 0.5) ** 2 <= 8.5**2
    ]
    for center_x, center_y in candidates:
        marker_x = max(left, min(center_x - 8, left + width - 16))
        marker_y = max(top, min(center_y - 8, top + height - 16))
        x0, y0 = marker_x - left, marker_y - top
        x1, y1 = min(x0 + 16, width), min(y0 + 16, height)
        coverage = (
            sums[y1 * stride + x1]
            - sums[y0 * stride + x1]
            - sums[y1 * stride + x0]
            + sums[y0 * stride + x0]
        )
        if coverage < len(circle_pixels):
            continue
        circle_coverage = sum(
            owners[(marker_y + 8 + dy) * WIDTH + marker_x + 8 + dx] == label
            for dx, dy in circle_pixels
        )
        if circle_coverage != len(circle_pixels):
            continue
        circle = QPainterPath()
        circle.addEllipse(QRectF(marker_x - 0.5, marker_y - 0.5, 17, 17))
        if not country_shape.contains(circle):
            continue
        clear = _reserved_pixels(marker_x, marker_y) == 0
        if not clear:
            clear = not any(circle.intersects(path) for path in reservations)
        if clear:
            return marker_x - left, marker_y - top
    raise ValueError(f"No hay espacio para la ficha y el nombre de {name}")


def _write_country_assets(
    owners: bytearray, names: list[str]
) -> tuple[dict[str, tuple[int, int, int, int]], list[tuple[str, int, int, str]]]:
    bounds = _country_bounds(owners, len(names))
    placements = {
        name: _marker_position(owners, label, bounds[label - 1], name)
        for label, name in enumerate(names, start=1)
    }
    marker_positions.update(placements)
    layouts = {}
    outlines = []
    for label, name in enumerate(names, start=1):
        left, top, width, height = bounds[label - 1]
        path = _outline_path(owners, label, bounds[label - 1])
        continent = continent_for[name]
        color = CONTINENTS[continent]["fill"]
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{name}">
  <defs><radialGradient id="wash" cx="0.48" cy="0.45" r="0.72"><stop stop-color="{lighten(color, 0.66)}"/><stop offset="0.55" stop-color="{lighten(color, 0.44)}"/><stop offset="0.82" stop-color="{lighten(color, 0.16)}"/><stop offset="1" stop-color="{color}"/></radialGradient></defs>
  <path d="{path}" fill="url(#wash)" fill-rule="nonzero"/>
</svg>
"""
        (THEME / "countries" / f"{name}.svg").write_text(svg, encoding="utf-8")
        layouts[name] = (left, top, width, height)
        outlines.append((continent, left, top, path))
    return layouts, outlines


def update_positions(layouts: dict[str, tuple[int, int, int, int]]) -> None:
    path = THEME / "paises.toml"
    content = path.read_text(encoding="utf-8")
    content = content.replace(
        "# Composición aproximada a partir de la foto frontal del tablero.",
        "# Contornos del tablero de Revancha generados desde geometry/board-layout.toml.",
    )
    for country, (left, top, _width, _height) in layouts.items():
        section = re.compile(
            rf"(?ms)(^\[[^\]]+\.{re.escape(country)}\]\n)(.*?)(?=^\[|\Z)"
        )
        match = section.search(content)
        if not match:
            raise ValueError(f"No se encontró la sección TOML de {country}")
        army_x, army_y = marker_positions[country]
        block = match.group(2)
        for key, value in (
            ("pos_x", left),
            ("pos_y", top),
            ("army_x", army_x),
            ("army_y", army_y),
        ):
            block, replacements = re.subn(
                rf"(?m)^{key}[ \t]*=[ \t]*-?\d+[ \t]*$",
                f"{key} = {value}",
                block,
                count=1,
            )
            if not replacements:
                raise ValueError(f"No se encontró {key} para {country}")
        content = content[: match.start(2)] + block + content[match.end(2) :]
    path.write_text(content, encoding="utf-8")


def touching_pairs(owners: bytearray, names: list[str]) -> set[frozenset[str]]:
    """Find borders in the same partition used to generate clickable countries."""
    touching = set()
    for y in range(HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            offset = y * WIDTH + x
            label = owners[offset]
            if not label:
                continue
            for step in (1, WIDTH - 1, WIDTH, WIDTH + 1):
                other = owners[offset + step]
                if other and label != other:
                    touching.add(frozenset((names[label - 1], names[other - 1])))
    return touching


def write_connections(owners: bytearray, names: list[str]) -> None:
    path = THEME / "adyacencias.toml"
    content = path.read_text(encoding="utf-8").split("# Rutas visuales:", 1)[0].rstrip()
    content += "\n\n# Rutas visuales: puentes confirmados en el grafo del tema.\n"
    explicit = {frozenset((entry[0], entry[1])) for entry in CONNECTIONS}
    missing = _allowed_pairs() - touching_pairs(owners, names) - explicit
    connections = [
        *CONNECTIONS,
        *((*sorted(pair), []) for pair in sorted(missing, key=sorted)),
    ]
    for origin, destination, source_points, *wrap in connections:
        if frozenset((origin, destination)) not in _allowed_pairs():
            raise ValueError(f"Ruta fuera del grafo: {origin} - {destination}")
        points = [scene_point(point) for point in source_points]
        content += f'\n[[ConexionesVisuales]]\norigen = "{origin}"\ndestino = "{destination}"\n'
        if wrap:
            content += 'envolver = "horizontal"\n'
            points = [(0.0, points[0][1]), (float(WIDTH), points[1][1])]
        content += (
            "puntos = [" + ", ".join(f"[{fmt(x)}, {fmt(y)}]" for x, y in points) + "]\n"
        )
    path.write_text(content, encoding="utf-8")


def label_svg(name: str) -> str:
    reservation, text, _x, _y, _angle, _size = label_geometry(name)
    path = painter_svg_path(label_glyphs(name))
    leader = ""
    anchor = BOARD[name].get("anclaje_etiqueta")
    if anchor:
        ax, ay = scene_point(anchor)
        rect = reservation.boundingRect()
        tx = max(rect.left(), min(ax, rect.right()))
        ty = max(rect.top(), min(ay, rect.bottom()))
        leader = f'<path d="M {fmt(ax)} {fmt(ay)} L {fmt(tx)} {fmt(ty)}" fill="none" stroke="{LABEL_INK}" stroke-width="1"/>'
    return f'{leader}<g id="country-label-{name}" aria-label="{text}"><path d="{path}" fill="{LABEL_HALO}" stroke="{LABEL_HALO}" stroke-width="2" stroke-linejoin="round"/><path d="{path}" fill="{LABEL_INK}"/></g>'


def write_landmass_layers(outlines: list[tuple[str, int, int, str]]) -> None:
    title = f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
    shell = [
        title,
        '<defs><radialGradient id="sea" cx="0.48" cy="0.4" r="0.75"><stop stop-color="#d9e4df"/><stop offset="0.52" stop-color="#c8dcdc"/><stop offset="1" stop-color="#abc7cf"/></radialGradient><radialGradient id="cloud"><stop stop-color="#f0ead4" stop-opacity="0.35"/><stop offset="0.5" stop-color="#f0ead4" stop-opacity="0.22"/><stop offset="1" stop-color="#f0ead4" stop-opacity="0"/></radialGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>',
    ]
    # Soft, translucent washes reproduce the pale water and worn paper tones.
    washes = [
        (180, 190, 128, 34),
        (303, 263, 101, 28),
        (310, 413, 106, 58),
        (369, 93, 114, 28),
        (699, 370, 64, 38),
        (297, 529, 110, 49),
        (486, 561, 109, 24),
        (84, 321, 56, 23),
        (607, 397, 57, 37),
    ]
    for x, y, rx, ry in washes:
        sx, sy = scene_point((x, y))
        shell.append(
            f'<ellipse cx="{fmt(sx)}" cy="{fmt(sy)}" rx="{fmt(rx * SCALE)}" ry="{fmt(ry * SCALE)}" fill="url(#cloud)"/>'
        )
    # The border is passive decoration, separate from click masks.
    shell.extend([
        f'<rect x="10" y="10" width="{WIDTH - 20}" height="{HEIGHT - 20}" fill="none" stroke="#9f4f62" stroke-width="2.5"/>',
        f'<rect x="15" y="15" width="{WIDTH - 30}" height="{HEIGHT - 30}" fill="none" stroke="#dac0ad" stroke-width="1.4"/>',
    ])
    shell.extend(
        f'<path d="M {x} 10 l 4 7 l 6 -1 M {x} {HEIGHT - 10} l -3 -7 l 7 -2" fill="none" stroke="#b85e76" stroke-width="2" opacity="0.65"/>'
        for x in range(28, WIDTH - 20, 43)
    )
    shell.extend(
        f'<path d="M 10 {y} l 7 -2 l -1 -5 M {WIDTH - 10} {y} l -7 3 l 1 6" fill="none" stroke="#b85e76" stroke-width="2" opacity="0.65"/>'
        for y in range(29, HEIGHT - 20, 43)
    )
    for text, x, y, angle in [
        ("OCÉANO", 75, 349, 0),
        ("PACÍFICO", 75, 361, 0),
        ("OCÉANO", 278, 345, 0),
        ("ATLÁNTICO", 278, 357, 0),
        ("OCÉANO PACÍFICO", 779, 269, 90),
    ]:
        sx, sy = scene_point((x, y))
        shell.append(
            f'<text x="{fmt(sx)}" y="{fmt(sy)}" transform="rotate({angle} {fmt(sx)} {fmt(sy)})" text-anchor="middle" font-family="Georgia,serif" font-size="14" letter-spacing="0.8" fill="#55666c">{text}</text>'
        )
    borders = [title]
    for continent, left, top, path in outlines:
        color = CONTINENTS[continent]["edge"]
        for width, opacity in ((9, 0.10), (5, 0.18), (2.3, 0.48), (0.8, 0.9)):
            borders.append(
                f'<path d="{path}" transform="translate({left} {top})" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
    borders.extend(label_svg(name) for name in BOARD)
    for stem, contents in (("shell", shell), ("borders", borders)):
        (THEME / "geometry" / f"revancha-{stem}.svg").write_text(
            "\n".join([*contents, "</svg>"]) + "\n", encoding="utf-8"
        )
    (THEME / "geometry" / "revancha-manifest.json").write_text(
        json.dumps(
            {
                "origin": [0.0, 0.0],
                "size": [WIDTH, HEIGHT],
                "background": "#abc7cf",
                "source": "board-layout.toml",
                "description": "Contornos vectoriales del mapa Revancha de Pyteg.",
                "label_ink": LABEL_INK,
                "label_halo": LABEL_HALO,
                "labels": {
                    name: {
                        "text": label_geometry(name)[1],
                        "font_family": LABEL_FONT,
                        "font_size": label_geometry(name)[5],
                        "reserved_polygon": [
                            [point.x(), point.y()]
                            for point in label_geometry(name)[0].toFillPolygon()
                        ],
                    }
                    for name in BOARD
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    _app = QGuiApplication.instance() or QGuiApplication([])
    if LABEL_FONT not in QFontDatabase.families():
        raise ValueError(
            f"Instalá {LABEL_FONT} para regenerar las etiquetas vectoriales"
        )
    _reserve_labels()
    countries_file = tomllib.loads((THEME / "paises.toml").read_text(encoding="utf-8"))
    for continent, countries in countries_file.items():
        if continent == "Distribucion":
            continue
        for name, country in countries.items():
            if isinstance(country, dict):
                continent_for[name] = continent
    if set(continent_for) != set(BOARD):
        raise ValueError("Los contornos deben cubrir exactamente los países del tema")
    base_assets = {name: make_country_mask(name) for name in continent_for}
    owners, names = _country_partition(base_assets)
    _separate_forbidden_contacts(owners, names)
    layouts, outlines = _write_country_assets(owners, names)
    update_positions(layouts)
    write_connections(owners, names)
    write_landmass_layers(outlines)


if __name__ == "__main__":
    main()
