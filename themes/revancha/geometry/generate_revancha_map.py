# ruff: noqa: D103, DOC201, DOC501, E501, EM101, EM102, INP001, PLR2004, TRY003
"""Genera una composición vectorial de Revancha desde una foto del tablero.

Las coordenadas de referencia usan la imagen frontal de 800 x 600 px compartida
durante el diseño. Las fronteras interiores son una partición geométrica
aproximada entre los centros visibles; no sustituyen el grafo de reglas.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[3]
THEME = ROOT / "themes" / "revancha"
SCALE = 1.77
WIDTH = 1416
HEIGHT = 1062
MARGIN = 3.0

CONTINENTS = {
    "AmericaDelNorte": {
        "fill": "#f1cf9b",
        "edge": "#a85c4d",
        "shell": [
            [
                (42, 127),
                (49, 102),
                (72, 91),
                (101, 88),
                (119, 101),
                (114, 119),
                (94, 129),
                (77, 146),
                (56, 154),
                (43, 143),
            ],
            [
                (45, 194),
                (54, 176),
                (63, 158),
                (72, 145),
                (91, 130),
                (110, 128),
                (131, 138),
                (151, 120),
                (170, 107),
                (194, 112),
                (210, 130),
                (232, 133),
                (249, 150),
                (265, 156),
                (279, 137),
                (296, 112),
                (311, 105),
                (309, 127),
                (294, 148),
                (277, 159),
                (264, 177),
                (261, 198),
                (253, 211),
                (252, 229),
                (245, 244),
                (241, 261),
                (231, 276),
                (222, 291),
                (214, 302),
                (202, 294),
                (193, 277),
                (177, 269),
                (159, 266),
                (146, 271),
                (135, 285),
                (125, 303),
                (113, 314),
                (101, 309),
                (90, 298),
                (76, 290),
                (65, 276),
                (57, 259),
                (50, 243),
                (45, 226),
                (49, 210),
                (43, 194),
            ],
            [
                (151, 108),
                (168, 100),
                (194, 104),
                (216, 111),
                (229, 122),
                (219, 137),
                (195, 137),
                (173, 132),
                (157, 123),
            ],
            [
                (243, 72),
                (259, 57),
                (280, 52),
                (304, 57),
                (316, 71),
                (309, 89),
                (297, 105),
                (279, 120),
                (262, 119),
                (246, 106),
                (237, 90),
            ],
        ],
    },
    "AmericaCentral": {
        "fill": "#ebd095",
        "edge": "#9d7950",
        "shell": [
            [
                (145, 259),
                (164, 255),
                (181, 261),
                (195, 273),
                (209, 285),
                (226, 296),
                (240, 303),
                (253, 314),
                (262, 329),
                (274, 342),
                (282, 352),
                (275, 361),
                (263, 354),
                (253, 342),
                (240, 333),
                (227, 322),
                (214, 311),
                (198, 303),
                (183, 292),
                (167, 283),
                (154, 273),
            ],
            [
                (198, 268),
                (207, 260),
                (226, 258),
                (244, 264),
                (256, 274),
                (250, 283),
                (232, 287),
                (213, 282),
                (200, 276),
            ],
            [(221, 307), (229, 304), (239, 308), (238, 315), (229, 318), (222, 314)],
        ],
    },
    "AmericaDelSur": {
        "fill": "#e7a18b",
        "edge": "#a54e43",
        "shell": [
            [
                (130, 408),
                (139, 390),
                (155, 379),
                (178, 375),
                (198, 379),
                (216, 373),
                (235, 379),
                (256, 386),
                (277, 396),
                (296, 410),
                (316, 426),
                (327, 443),
                (321, 463),
                (306, 478),
                (292, 492),
                (283, 511),
                (270, 529),
                (259, 549),
                (246, 570),
                (230, 589),
                (216, 598),
                (202, 582),
                (194, 559),
                (183, 539),
                (171, 518),
                (158, 495),
                (148, 475),
                (137, 454),
                (128, 433),
            ],
            [(169, 572), (177, 567), (184, 571), (182, 579), (174, 580)],
        ],
    },
    "Europa": {
        "fill": "#dda0c4",
        "edge": "#9b4c7a",
        "shell": [
            [
                (338, 128),
                (349, 116),
                (369, 115),
                (390, 122),
                (401, 133),
                (390, 149),
                (371, 155),
                (350, 150),
                (337, 140),
            ],
            [
                (345, 196),
                (354, 181),
                (367, 177),
                (378, 188),
                (376, 208),
                (365, 222),
                (350, 219),
                (342, 207),
            ],
            [
                (374, 180),
                (387, 169),
                (401, 174),
                (404, 197),
                (396, 215),
                (383, 215),
                (377, 202),
            ],
            [
                (407, 151),
                (421, 128),
                (443, 120),
                (465, 126),
                (483, 141),
                (500, 141),
                (520, 130),
                (543, 139),
                (557, 157),
                (553, 180),
                (545, 198),
                (541, 218),
                (530, 235),
                (514, 248),
                (507, 267),
                (493, 282),
                (485, 302),
                (468, 321),
                (450, 326),
                (436, 311),
                (423, 306),
                (406, 316),
                (391, 312),
                (383, 298),
                (364, 300),
                (346, 291),
                (337, 276),
                (344, 257),
                (356, 240),
                (365, 224),
                (377, 217),
                (385, 199),
                (397, 180),
            ],
        ],
    },
    "Africa": {
        "fill": "#e9a18e",
        "edge": "#a84f45",
        "shell": [
            [
                (358, 371),
                (371, 354),
                (390, 344),
                (411, 346),
                (429, 356),
                (448, 352),
                (466, 357),
                (485, 354),
                (505, 361),
                (525, 360),
                (546, 369),
                (560, 382),
                (571, 401),
                (565, 421),
                (555, 440),
                (546, 457),
                (536, 475),
                (525, 494),
                (512, 512),
                (499, 526),
                (484, 533),
                (468, 523),
                (451, 517),
                (432, 515),
                (415, 519),
                (398, 512),
                (383, 506),
                (368, 492),
                (356, 475),
                (346, 456),
                (344, 435),
                (350, 415),
                (347, 394),
            ],
            [
                (581, 451),
                (590, 458),
                (593, 477),
                (589, 497),
                (583, 507),
                (577, 495),
                (575, 475),
            ],
        ],
    },
    "Asia": {
        "fill": "#d8d09e",
        "edge": "#837c4e",
        "shell": [
            [
                (531, 110),
                (544, 92),
                (565, 81),
                (591, 70),
                (620, 66),
                (648, 70),
                (674, 67),
                (701, 77),
                (723, 74),
                (744, 86),
                (756, 106),
                (748, 126),
                (758, 145),
                (747, 163),
                (735, 178),
                (740, 197),
                (733, 218),
                (742, 240),
                (733, 261),
                (741, 284),
                (730, 307),
                (718, 324),
                (700, 336),
                (685, 351),
                (669, 357),
                (650, 350),
                (639, 337),
                (625, 332),
                (611, 348),
                (594, 354),
                (579, 346),
                (568, 332),
                (554, 327),
                (545, 310),
                (541, 294),
                (529, 281),
                (532, 264),
                (524, 246),
                (530, 225),
                (525, 206),
                (532, 188),
                (523, 168),
                (530, 147),
            ],
            [
                (710, 173),
                (720, 168),
                (730, 178),
                (735, 198),
                (731, 221),
                (725, 242),
                (717, 246),
                (712, 226),
                (708, 203),
            ],
        ],
    },
    "Oceania": {
        "fill": "#9ed1c6",
        "edge": "#558d83",
        "shell": [
            [
                (627, 379),
                (640, 371),
                (653, 377),
                (658, 391),
                (650, 406),
                (636, 414),
                (625, 405),
            ],
            [
                (687, 392),
                (704, 390),
                (724, 399),
                (735, 411),
                (726, 421),
                (710, 417),
                (696, 410),
            ],
            [
                (751, 419),
                (770, 414),
                (790, 421),
                (800, 435),
                (790, 446),
                (771, 445),
                (757, 437),
            ],
            [
                (610, 456),
                (628, 448),
                (651, 453),
                (672, 449),
                (696, 455),
                (715, 469),
                (719, 487),
                (709, 505),
                (700, 523),
                (683, 536),
                (662, 540),
                (643, 532),
                (626, 521),
                (612, 503),
                (604, 482),
            ],
            [(660, 546), (674, 542), (687, 549), (688, 561), (677, 568), (664, 563)],
            [
                (567, 551),
                (584, 545),
                (606, 548),
                (628, 551),
                (650, 558),
                (642, 570),
                (620, 574),
                (600, 569),
                (582, 565),
                (568, 560),
            ],
        ],
    },
}

# Centers are taken from the visible territory labels in the supplied photo.
CENTERS = {
    "California": (101, 287),
    "NuevaYork": (225, 184),
    "LasVegas": (119, 247),
    "Florida": (205, 276),
    "Chicago": (202, 230),
    "Terranova": (176, 164),
    "Labrador": (224, 148),
    "Canada": (139, 164),
    "Oregon": (130, 211),
    "IslaVictoria": (191, 119),
    "Alaska": (89, 113),
    "Groenlandia": (276, 87),
    "Mexico": (193, 286),
    "Honduras": (245, 315),
    "ElSalvador": (251, 328),
    "Nicaragua": (267, 346),
    "Cuba": (226, 273),
    "Jamaica": (231, 312),
    "Brasil": (278, 475),
    "Argentina": (215, 529),
    "Uruguay": (263, 535),
    "Chile": (181, 518),
    "Colombia": (178, 426),
    "Bolivia": (211, 496),
    "Paraguay": (246, 514),
    "Venezuela": (225, 432),
    "Islandia": (370, 134),
    "Irlanda": (358, 203),
    "GranBretana": (390, 194),
    "Noruega": (440, 145),
    "Finlandia": (482, 151),
    "Bielorrusia": (519, 137),
    "Portugal": (348, 300),
    "Espana": (375, 296),
    "Francia": (420, 282),
    "Alemania": (452, 260),
    "Italia": (452, 308),
    "Croacia": (475, 281),
    "Serbia": (495, 260),
    "Polonia": (501, 216),
    "Albania": (487, 299),
    "Ucrania": (538, 200),
    "Sahara": (391, 433),
    "Egipto": (489, 373),
    "Etiopia": (478, 414),
    "Nigeria": (440, 457),
    "Angola": (516, 448),
    "Mauritania": (531, 478),
    "Madagascar": (584, 481),
    "Sudafrica": (511, 511),
    "Rusia": (578, 179),
    "Siberia": (587, 96),
    "Chechenia": (645, 101),
    "Chukchi": (588, 134),
    "Kamchatka": (670, 191),
    "Iran": (561, 237),
    "Irak": (579, 270),
    "China": (621, 222),
    "Corea": (682, 220),
    "Japon": (725, 201),
    "Malasia": (616, 289),
    "Turquia": (543, 284),
    "Israel": (565, 312),
    "Arabia": (588, 340),
    "India": (619, 339),
    "Vietnam": (674, 326),
    "Sumatra": (642, 392),
    "Filipinas": (710, 405),
    "Tonga": (777, 431),
    "Australia": (671, 490),
    "Tasmania": (674, 555),
    "NuevaZelandia": (608, 559),
}

DISPLAY_NAMES = {
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

CONNECTIONS = [
    ("Alaska", "Chukchi", [(305, 77), (443, 78)]),
    ("Alaska", "Kamchatka", [(279, 157), (432, 168), (531, 161)]),
    ("Groenlandia", "Islandia", [(326, 128)]),
    ("California", "Tonga", [(0, 294), (800, 422)], "horizontal"),
    ("Brasil", "Sahara", [(337, 429)]),
    ("Uruguay", "Nigeria", [(310, 502)]),
    ("Espana", "Sahara", [(377, 347)]),
    ("Polonia", "Egipto", [(500, 281), (490, 340)]),
    ("Chile", "Australia", [(0, 520), (800, 494)], "horizontal"),
    ("India", "Sumatra", [(628, 366)]),
    ("Filipinas", "Australia", [(704, 431)]),
]


def scene_point(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] * SCALE, point[1] * SCALE


def fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def svg_path(points: list[tuple[float, float]]) -> str:
    commands = [f"M {fmt(points[0][0])} {fmt(points[0][1])}"]
    commands.extend(f"L {fmt(x)} {fmt(y)}" for x, y in points[1:])
    return " ".join(commands) + " Z"


def horizontal_span(
    polygon: list[tuple[float, float]], y: float
) -> tuple[float, float] | None:
    intersections: list[float] = []
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(index + 1) % len(polygon)]
        if (y1 <= y < y2) or (y2 <= y < y1):
            ratio = (y - y1) / (y2 - y1)
            intersections.append(x1 + ratio * (x2 - x1))
    if len(intersections) < 2:
        return None
    return min(intersections), max(intersections)


def point_in_contours(
    point: tuple[float, float], contours: list[list[tuple[float, float]]]
) -> bool:
    x, y = point
    for polygon in contours:
        inside = False
        previous = polygon[-1]
        for current in polygon:
            x1, y1 = previous
            x2, y2 = current
            if (y1 > y) != (y2 > y):
                crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
                if x < crossing_x:
                    inside = not inside
            previous = current
        if inside:
            return True
    return False


def clip_half_plane(
    polygon: list[tuple[float, float]], a: float, b: float, c: float
) -> list[tuple[float, float]]:
    if not polygon:
        return []
    result: list[tuple[float, float]] = []
    previous = polygon[-1]
    previous_value = a * previous[0] + b * previous[1] - c
    for current in polygon:
        current_value = a * current[0] + b * current[1] - c
        previous_inside = previous_value <= 1e-8
        current_inside = current_value <= 1e-8
        if previous_inside != current_inside:
            denominator = previous_value - current_value
            if denominator:
                ratio = previous_value / denominator
                result.append((
                    previous[0] + ratio * (current[0] - previous[0]),
                    previous[1] + ratio * (current[1] - previous[1]),
                ))
        if current_inside:
            result.append(current)
        previous = current
        previous_value = current_value
    return result


def polygon_area(polygon: list[tuple[float, float]]) -> float:
    return (
        sum(
            first[0] * second[1] - second[0] * first[1]
            for first, second in zip(polygon, polygon[1:] + polygon[:1], strict=True)
        )
        / 2
    )


def cross_product(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
        third[0] - first[0]
    )


def _inside_triangle(
    point: tuple[float, float],
    triangle: list[tuple[float, float]],
    orientation: float,
) -> bool:
    crosses = [
        cross_product(triangle[index], triangle[(index + 1) % 3], point) * orientation
        for index in range(3)
    ]
    return all(value > 1e-8 for value in crosses)


def triangulate(polygon: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
    """Split a simple coastline polygon into triangles using ear clipping."""
    orientation = 1.0 if polygon_area(polygon) > 0 else -1.0
    vertices = list(range(len(polygon)))
    triangles: list[list[tuple[float, float]]] = []
    while len(vertices) > 3:
        ear_found = False
        for offset, current_index in enumerate(vertices):
            previous_index = vertices[offset - 1]
            next_index = vertices[(offset + 1) % len(vertices)]
            triangle = [
                polygon[previous_index],
                polygon[current_index],
                polygon[next_index],
            ]
            if cross_product(*triangle) * orientation <= 1e-8:
                continue
            if any(
                _inside_triangle(polygon[index], triangle, orientation)
                for index in vertices
                if index not in {previous_index, current_index, next_index}
            ):
                continue
            triangles.append(triangle)
            del vertices[offset]
            ear_found = True
            break
        if ear_found:
            continue

        # Drop a collinear vertex if the contour contains a redundant point.
        for offset, current_index in enumerate(vertices):
            previous_index = vertices[offset - 1]
            next_index = vertices[(offset + 1) % len(vertices)]
            if (
                abs(
                    cross_product(
                        polygon[previous_index],
                        polygon[current_index],
                        polygon[next_index],
                    )
                )
                < 1e-7
            ):
                del vertices[offset]
                ear_found = True
                break
        if not ear_found:
            raise ValueError("No se pudo triangular un contorno del mapa")

    triangles.append([polygon[index] for index in vertices])
    return triangles


def intersect_with_shell(
    polygon: list[tuple[float, float]],
    contours: list[list[tuple[float, float]]],
) -> list[list[tuple[float, float]]]:
    """Clip a territory against triangulated coastline polygons."""
    pieces = []
    for contour in contours:
        for triangle in triangulate(contour):
            clipped = polygon
            orientation = 1 if polygon_area(triangle) > 0 else -1
            for index, first in enumerate(triangle):
                second = triangle[(index + 1) % len(triangle)]
                dx, dy = second[0] - first[0], second[1] - first[1]
                if orientation > 0:
                    a, b = dy, -dx
                    c = dy * first[0] - dx * first[1]
                else:
                    a, b = -dy, dx
                    c = -dy * first[0] + dx * first[1]
                clipped = clip_half_plane(clipped, a, b, c)
                if not clipped:
                    break
            if len(clipped) >= 3 and abs(polygon_area(clipped)) > 0.02:
                pieces.append(clipped)
    return pieces


def voronoi_cell(name: str, names: list[str]) -> list[tuple[float, float]]:
    all_points = [
        point
        for contour in CONTINENTS[continent_for[name]]["shell"]
        for point in contour
    ]
    min_x = min(point[0] for point in all_points) - 8
    min_y = min(point[1] for point in all_points) - 8
    max_x = max(point[0] for point in all_points) + 8
    max_y = max(point[1] for point in all_points) + 8
    cell = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    x, y = CENTERS[name]
    for other in names:
        if other == name:
            continue
        ox, oy = CENTERS[other]
        cell = clip_half_plane(
            cell,
            2 * (ox - x),
            2 * (oy - y),
            ox * ox + oy * oy - x * x - y * y,
        )
    return cell


continent_for: dict[str, str] = {}


def jagged_cell(  # noqa: PLR0914
    name: str, cell: list[tuple[float, float]], names: list[str]
) -> tuple[list[tuple[float, float]], list[tuple[str, list[tuple[float, float]]]]]:
    result: list[tuple[float, float]] = []
    shared_edges: list[tuple[str, list[tuple[float, float]]]] = []
    x, y = CENTERS[name]
    for index, first in enumerate(cell):
        second = cell[(index + 1) % len(cell)]
        result.append(first)
        neighbor = None
        for other in names:
            if other == name:
                continue
            ox, oy = CENTERS[other]
            constant = ox * ox + oy * oy - x * x - y * y
            if all(
                abs(2 * (ox - x) * point[0] + 2 * (oy - y) * point[1] - constant) < 0.01
                for point in (first, second)
            ):
                neighbor = other
                break
        if neighbor is None:
            continue
        identity = "\0".join(sorted((name, neighbor))).encode()
        digest = hashlib.sha1(identity, usedforsecurity=False).digest()
        first_name, second_name = sorted((name, neighbor))
        fx, fy = CENTERS[first_name]
        sx, sy = CENTERS[second_name]
        dx, dy = sx - fx, sy - fy
        length = math.hypot(dx, dy) or 1
        normal = (-dy / length, dx / length)
        samples = ((1 / 3, digest[0]), (2 / 3, digest[1]))
        if first > second:
            samples = tuple(reversed(samples))
        edge_points = [first]
        for sample, byte in samples:
            amount = (byte / 255 * 2 - 1) * 3.2
            midpoint = (
                first[0] + (second[0] - first[0]) * sample,
                first[1] + (second[1] - first[1]) * sample,
            )
            point = (
                midpoint[0] + normal[0] * amount,
                midpoint[1] + normal[1] * amount,
            )
            result.append(point)
            edge_points.append(point)
        edge_points.append(second)
        shared_edges.append((neighbor, edge_points))
    return result, shared_edges


def lighten(color: str, fraction: float) -> str:
    channels = [int(color[index : index + 2], 16) for index in (1, 3, 5)]
    return "#" + "".join(
        f"{round(channel + (255 - channel) * fraction):02x}" for channel in channels
    )


def make_country_svg(  # noqa: PLR0914
    name: str,
    continent: str,
    cell: list[tuple[float, float]],
    neighbors: list[str],
) -> tuple[
    str,
    tuple[int, int, int, int],
    tuple[float, float, float, str],
    list[tuple[str, list[tuple[float, float]]]],
]:
    cell, shared_edges = jagged_cell(name, cell, neighbors)
    pieces = intersect_with_shell(cell, CONTINENTS[continent]["shell"])
    if not pieces:
        raise ValueError(f"El país {name} no intersecta la masa terrestre asignada")
    scaled_pieces = [[scene_point(point) for point in piece] for piece in pieces]
    scaled = [point for piece in scaled_pieces for point in piece]
    left = math.floor(min(point[0] for point in scaled) - MARGIN)
    top = math.floor(min(point[1] for point in scaled) - MARGIN)
    right = math.ceil(max(point[0] for point in scaled) + MARGIN)
    bottom = math.ceil(max(point[1] for point in scaled) + MARGIN)
    width, height = right - left, bottom - top
    path = " ".join(
        svg_path([(x - left, y - top) for x, y in piece]) for piece in scaled_pieces
    )
    seed_x, seed_y = CENTERS[name]
    color = CONTINENTS[continent]["fill"]
    label = DISPLAY_NAMES.get(
        name, name.replace("Del", " del ").replace("De", " de ")
    ).upper()
    contours = CONTINENTS[continent]["shell"]
    label_candidates = []
    for offset in range(-6, 7):
        candidate_y = seed_y + offset
        span = horizontal_span(cell, candidate_y)
        if span is None:
            continue
        center_x = (span[0] + span[1]) / 2
        if not point_in_contours((center_x, candidate_y), contours):
            continue
        width_scene = (span[1] - span[0]) * SCALE
        score = width_scene - abs(offset) * 3
        label_candidates.append((score, center_x, candidate_y, width_scene))
    if label_candidates:
        _score, label_x_source, label_y_source, label_width = max(label_candidates)
    else:
        label_x_source, label_y_source = seed_x, seed_y
        label_width = width * 0.68
    font_size = max(8.0, min(12.0, label_width * 0.72 / max(4, len(label) * 0.68)))
    label_x, label_y = scene_point((label_x_source, label_y_source))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{label.title()}">
  <defs>
    <linearGradient id="wash" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0" stop-color="{lighten(color, 0.20)}"/>
      <stop offset="0.55" stop-color="{lighten(color, 0.08)}"/>
      <stop offset="1" stop-color="{color}"/>
    </linearGradient>
  </defs>
  <path d="{path}" fill="url(#wash)" stroke="none" fill-rule="nonzero"/>
</svg>
"""
    return (
        svg,
        (left, top, width, height),
        (label_x, label_y, font_size, label),
        shared_edges,
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


def _marker_position(  # noqa: PLR0914
    owners: bytearray, label: int, bounds: tuple[int, int, int, int], name: str
) -> tuple[int, int]:
    """Find the best 16-pixel marker site inside its own country."""
    left, top, width, height = bounds
    stride = width + 1
    sums = [0] * (stride * (height + 1))
    candidates: list[tuple[int, int]] = []
    for y in range(height):
        running = 0
        for x in range(width):
            scene_x, scene_y = left + x, top + y
            is_own = owners[scene_y * WIDTH + scene_x] == label
            running += is_own
            sums[(y + 1) * stride + x + 1] = sums[y * stride + x + 1] + running
            if is_own:
                candidates.append((scene_x, scene_y))

    target_x, target_y = scene_point(CENTERS[name])
    best_score = (-1, float("-inf"))
    best = candidates[0]
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
        distance = (center_x - target_x) ** 2 + (center_y - target_y) ** 2
        score = (coverage, -distance)
        if score > best_score:
            best_score = score
            best = (marker_x, marker_y)
    return best[0] - left, best[1] - top


def _write_country_assets(  # noqa: PLR0914
    owners: bytearray,
    names: list[str],
    labels: dict[str, tuple[float, float, float, str]],
) -> tuple[dict[str, tuple[int, int, int, int]], list[tuple[str, int, int, str]]]:
    bounds = _country_bounds(owners, len(names))
    layouts: dict[str, tuple[int, int, int, int]] = {}
    outlines: list[tuple[str, int, int, str]] = []
    for label, name in enumerate(names, start=1):
        left, top, width, height = bounds[label - 1]
        path = _outline_path(owners, label, bounds[label - 1])
        continent = continent_for[name]
        color = CONTINENTS[continent]["fill"]
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{name}">
  <defs><linearGradient id="wash" x1="0" y1="0" x2="0.9" y2="1"><stop offset="0" stop-color="{lighten(color, 0.20)}"/><stop offset="0.55" stop-color="{lighten(color, 0.08)}"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>
  <path d="{path}" fill="url(#wash)" fill-rule="nonzero"/>
</svg>
"""
        (THEME / "countries" / f"{name}.svg").write_text(svg, encoding="utf-8")
        layouts[name] = (left, top, width, height)
        outlines.append((continent, left, top, path))
        army_x, army_y = _marker_position(owners, label, bounds[label - 1], name)
        _old_x, _old_y, font_size, text = labels[name]
        labels[name] = (left + army_x + 8, top + army_y - 3, font_size, text)
        marker_positions[name] = (army_x, army_y)
    return layouts, outlines


marker_positions: dict[str, tuple[int, int]] = {}


def update_positions(layouts: dict[str, tuple[int, int, int, int]]) -> None:
    path = THEME / "paises.toml"
    content = path.read_text(encoding="utf-8")
    content = content.replace(
        "# Distribución esquemática del mapa de TEG La Revancha.",
        "# Composición aproximada a partir de la foto frontal del tablero.",
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


def write_connections() -> None:
    path = THEME / "adyacencias.toml"
    content = path.read_text(encoding="utf-8")
    content = (
        content.split("# Rutas visuales:", 1)[0].rstrip()
        + "\n\n# Rutas visuales: puentes confirmados en el grafo del tema.\n"
    )
    for entry in CONNECTIONS:
        origin, destination, source_points, *wrap = entry
        points = [scene_point(point) for point in source_points]
        content += "\n[[ConexionesVisuales]]\n"
        content += f'origen = "{origin}"\ndestino = "{destination}"\n'
        if wrap:
            content += 'envolver = "horizontal"\n'
            points = [(0.0, points[0][1]), (float(WIDTH), points[1][1])]
        content += (
            "puntos = [" + ", ".join(f"[{fmt(x)}, {fmt(y)}]" for x, y in points) + "]\n"
        )
    path.write_text(content, encoding="utf-8")


def write_landmass_layers(
    labels: dict[str, tuple[float, float, float, str]],
    outlines: list[tuple[str, int, int, str]],
) -> None:
    background = [
        ("OCÉANO PACÍFICO", 92, 345),
        ("OCÉANO ATLÁNTICO", 300, 342),
        ("OCÉANO ÍNDICO", 586, 425),
    ]
    title = f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
    shell = [
        title,
        '<defs><linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d6e8e7"/><stop offset="1" stop-color="#c9e0e2"/></linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>',
    ]
    borders = [title]
    for label, x, y in background:
        sx, sy = scene_point((x, y))
        shell.append(
            f'<text x="{fmt(sx)}" y="{fmt(sy)}" text-anchor="middle" font-family="Georgia,serif" font-size="17" letter-spacing="2" fill="#789698" opacity="0.78">{label}</text>'
        )
    for continent, left, top, path in outlines:
        color = CONTINENTS[continent]["edge"]
        borders.append(
            f'<path d="{path}" transform="translate({left} {top})" '
            f'fill="none" stroke="{color}" stroke-width="1.4" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for x, y, font_size, label in labels.values():
        attrs = (
            f'x="{fmt(x)}" y="{fmt(y)}" text-anchor="middle" '
            f'font-family="Arial,sans-serif" font-size="{fmt(font_size)}" '
            'font-weight="700"'
        )
        label_backdrop = (
            f'<text {attrs} fill="none" stroke="#f9f4e8" '
            f'stroke-width="2.2" stroke-linejoin="round">{label}</text>'
        )
        borders.extend((label_backdrop, f'<text {attrs} fill="#39362f">{label}</text>'))
    shell.append("</svg>")
    borders.append("</svg>")
    (THEME / "geometry" / "revancha-shell.svg").write_text(
        "\n".join(shell) + "\n", encoding="utf-8"
    )
    (THEME / "geometry" / "revancha-borders.svg").write_text(
        "\n".join(borders) + "\n", encoding="utf-8"
    )
    (THEME / "geometry" / "revancha-manifest.json").write_text(
        json.dumps(
            {
                "origin": [0.0, 0.0],
                "size": [WIDTH, HEIGHT],
                "description": "Composición original aproximada desde la foto frontal del tablero de Revancha.",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    countries_file = tomllib.loads((THEME / "paises.toml").read_text(encoding="utf-8"))
    country_names = [
        country
        for continent, countries in countries_file.items()
        if continent != "Distribucion"
        for country, data in countries.items()
        if isinstance(data, dict)
    ]
    for continent, countries in countries_file.items():
        if continent == "Distribucion":
            continue
        for country, data in countries.items():
            if isinstance(data, dict):
                continent_for[country] = continent
    missing = set(country_names) - set(CENTERS)
    extra = set(CENTERS) - set(country_names)
    if missing or extra:
        raise ValueError(
            f"Centros inconsistentes: faltan={sorted(missing)}, sobran={sorted(extra)}"
        )

    base_assets: dict[str, tuple[str, tuple[int, int, int, int]]] = {}
    labels: dict[str, tuple[float, float, float, str]] = {}
    for continent, countries in countries_file.items():
        if continent == "Distribucion":
            continue
        names = [
            country for country, data in countries.items() if isinstance(data, dict)
        ]
        for country in names:
            cell = voronoi_cell(country, names)
            svg, bounds, label, _shared_edges = make_country_svg(
                country, continent, cell, names
            )
            base_assets[country] = svg, bounds
            labels[country] = label
    owners, country_names = _country_partition(base_assets)
    _separate_forbidden_contacts(owners, country_names)
    layouts, outlines = _write_country_assets(owners, country_names, labels)
    update_positions(layouts)
    write_connections()
    write_landmass_layers(labels, outlines)


if __name__ == "__main__":
    main()
