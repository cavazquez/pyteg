"""Detección de superposiciones entre sprites de países del mapa."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_ALPHA_THRESHOLD = 32
_SOLID_ALPHA_THRESHOLD = 128
_PAIR_SIZE = 2


@dataclass(frozen=True)
class PaisBounds:
    """Rectángulo absoluto de un país en coordenadas de escena."""

    name: str
    continent: str
    left: float
    top: float
    width: int
    height: int
    z_index: int
    image_path: Path

    @property
    def right(self) -> float:
        """Borde derecho en coordenadas de escena."""
        return self.left + self.width

    @property
    def bottom(self) -> float:
        """Borde inferior en coordenadas de escena."""
        return self.top + self.height


@dataclass(frozen=True)
class BboxOverlap:
    """Superposición de bounding boxes entre dos países."""

    top: PaisBounds
    bottom: PaisBounds
    area: float


@dataclass(frozen=True)
class PixelOverlap:
    """Superposición de píxeles opacos entre dos países."""

    top: PaisBounds
    bottom: PaisBounds
    opaque_pixels: int


@dataclass(frozen=True)
class BoundaryGap:
    """Frontera terrestre declarada cuyos interiores no llegan a tocarse."""

    first: PaisBounds
    second: PaisBounds


def _intersection_area(a: PaisBounds, b: PaisBounds) -> float:
    dx = min(a.right, b.right) - max(a.left, b.left)
    dy = min(a.bottom, b.bottom) - max(a.top, b.top)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def load_pais_bounds(theme: str, *, folder: str = "themes/") -> list[PaisBounds]:
    """Carga posición absoluta y tamaño de cada país desde TOML + asset.

    Returns:
        Lista de bounds en orden de apilamiento (z_index creciente).

    Raises:
        OSError: Si algún asset del tema no se puede cargar.

    """
    reader = TomlReader.from_theme(theme, strict=True)
    bounds: list[PaisBounds] = []
    z_index = 0

    for continente in reader.get_continentes():
        cor_x, cor_y = reader.coordenadas_continente(continente)
        for pais in reader.get_paises(continente):
            pos_x, pos_y, _, _ = reader.coordenadas(pais)
            image_path = Path(get_resource_path(folder + reader.img_path(pais)))
            image = QImage(str(image_path))
            if image.isNull():
                msg = f"No se pudo cargar la imagen de {pais}: {image_path}"
                raise OSError(msg)

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


def find_bbox_overlaps(bounds: list[PaisBounds]) -> list[BboxOverlap]:
    """Pares de países cuyos rectángulos se intersectan (z_index mayor = encima).

    Returns:
        Lista ordenada por área de intersección descendente.

    """
    overlaps: list[BboxOverlap] = []
    for i, a in enumerate(bounds):
        for b in bounds[i + 1 :]:
            area = _intersection_area(a, b)
            if area <= 0:
                continue
            top, bottom = (b, a) if b.z_index > a.z_index else (a, b)
            overlaps.append(BboxOverlap(top=top, bottom=bottom, area=area))
    overlaps.sort(key=lambda item: item.area, reverse=True)
    return overlaps


def _mask_at(
    bounds: PaisBounds, image: QImage, *, alpha_threshold: int
) -> set[tuple[int, int]]:
    """Construye la máscara opaca de un sprite en coordenadas de escena.

    Returns:
        Coordenadas de escena de los píxeles que superan el alpha indicado.

    """
    return {
        (int(bounds.left) + x, int(bounds.top) + y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() >= alpha_threshold
    }


def _masks(
    bounds: list[PaisBounds], *, alpha_threshold: int, ignore_strokes: bool = False
) -> dict[str, set[tuple[int, int]]]:
    images = {
        item.name: _load_image(item.image_path, ignore_strokes=ignore_strokes)
        for item in bounds
    }
    return {
        item.name: _mask_at(item, images[item.name], alpha_threshold=alpha_threshold)
        for item in bounds
    }


@lru_cache(maxsize=128)
def _load_image(path: Path, *, ignore_strokes: bool = False) -> QImage:
    """Carga un sprite y, para SVG, puede separar el relleno del contorno.

    El contorno es una línea de dibujo compartida y no representa territorio.
    Por eso el análisis estricto mide los rellenos sin contar como solapamiento
    que los trazos de dos países vecinos coincidan sobre su frontera.

    Returns:
        Imagen rasterizada del sprite, opcionalmente sin los trazos del SVG.

    """
    if not ignore_strokes or path.suffix.lower() != ".svg":
        return QImage(str(path))

    source = path.read_text(encoding="utf-8")
    fill_only = re.sub(r"\bstroke\s*=\s*['\"][^'\"]*['\"]", 'stroke="none"', source)
    renderer = QSvgRenderer(QByteArray(fill_only.encode("utf-8")))
    if not renderer.isValid():
        return QImage(str(path))

    size = renderer.defaultSize()
    if not size.isValid() or size.width() <= 0 or size.height() <= 0:
        return QImage(str(path))

    image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def _masks_touch(
    first: set[tuple[int, int]], second: set[tuple[int, int]], radius: int
) -> bool:
    """Indica si dos máscaras se tocan o quedan a ``radius`` píxeles.

    Returns:
        ``True`` si las máscaras se intersectan o están dentro del radio.

    """
    if first & second:
        return True
    smaller, larger = (first, second) if len(first) <= len(second) else (second, first)
    for x, y in smaller:
        for offset_x in range(-radius, radius + 1):
            for offset_y in range(-radius, radius + 1):
                if (x + offset_x, y + offset_y) in larger:
                    return True
    return False


def count_opaque_overlap(
    a: PaisBounds,
    image_a: QImage,
    b: PaisBounds,
    image_b: QImage,
    *,
    alpha_threshold: int = _ALPHA_THRESHOLD,
) -> int:
    """Cuenta píxeles opacos compartidos en la intersección de dos países.

    Returns:
        Cantidad de píxeles donde ambos sprites son opacos.

    """
    left = int(max(a.left, b.left))
    top = int(max(a.top, b.top))
    right = int(min(a.right, b.right))
    bottom = int(min(a.bottom, b.bottom))
    if left >= right or top >= bottom:
        return 0

    count = 0
    for scene_y in range(top, bottom):
        for scene_x in range(left, right):
            ax = scene_x - int(a.left)
            ay = scene_y - int(a.top)
            bx = scene_x - int(b.left)
            by = scene_y - int(b.top)
            if (
                image_a.pixelColor(ax, ay).alpha() >= alpha_threshold
                and image_b.pixelColor(bx, by).alpha() >= alpha_threshold
            ):
                count += 1
    return count


def find_pixel_overlaps(
    bounds: list[PaisBounds],
    *,
    min_pixels: int = 1,
    alpha_threshold: int = _ALPHA_THRESHOLD,
    ignore_strokes: bool = False,
) -> list[PixelOverlap]:
    """Pares con píxeles opacos superpuestos (más preciso que solo bbox).

    Returns:
        Lista ordenada por cantidad de píxeles opacos descendente.

    """
    overlaps: list[PixelOverlap] = []
    images = {
        item.name: _load_image(item.image_path, ignore_strokes=ignore_strokes)
        for item in bounds
    }

    for i, a in enumerate(bounds):
        for b in bounds[i + 1 :]:
            pixels = count_opaque_overlap(
                a,
                images[a.name],
                b,
                images[b.name],
                alpha_threshold=alpha_threshold,
            )
            if pixels < min_pixels:
                continue
            top, bottom = (b, a) if b.z_index > a.z_index else (a, b)
            overlaps.append(PixelOverlap(top=top, bottom=bottom, opaque_pixels=pixels))

    overlaps.sort(key=lambda item: item.opaque_pixels, reverse=True)
    return overlaps


def find_solid_overlaps(
    bounds: list[PaisBounds], *, min_pixels: int = 1
) -> list[PixelOverlap]:
    """Encuentra solapamientos entre los interiores sólidos de los sprites.

    Para SVG se omite el trazo de frontera: dos países pueden dibujar el mismo
    límite compartido sin que ninguno tape el relleno del otro.

    Returns:
        Solapamientos ordenados por cantidad de píxeles sólidos compartidos.

    """
    return find_pixel_overlaps(
        bounds,
        min_pixels=min_pixels,
        alpha_threshold=_SOLID_ALPHA_THRESHOLD,
        ignore_strokes=True,
    )


def find_unconnected_boundaries(
    bounds: list[PaisBounds],
    adjacencies: Mapping[str, Sequence[str]],
    visual_connections: Iterable[tuple[str, str]] = (),
    *,
    max_gap: int = 1,
) -> list[BoundaryGap]:
    """Encuentra fronteras terrestres declaradas cuyas siluetas no se tocan.

    Las aristas representadas por ``visual_connections`` se excluyen porque
    atraviesan agua o el salto de los extremos del mapa y deben unirse con una
    línea, no con contacto entre las siluetas.

    Returns:
        Pares de países separados por más de ``max_gap`` píxeles.

    Raises:
        ValueError: Si ``max_gap`` es negativo.

    """
    if max_gap < 0:
        msg = "max_gap debe ser mayor o igual que cero"
        raise ValueError(msg)

    by_name = {item.name: item for item in bounds}
    masks = _masks(bounds, alpha_threshold=_SOLID_ALPHA_THRESHOLD)
    visual_pairs = {frozenset(pair) for pair in visual_connections}
    seen: set[frozenset[str]] = set()
    gaps: list[BoundaryGap] = []

    for origin, destinations in adjacencies.items():
        for destination in destinations:
            pair = frozenset((origin, destination))
            if len(pair) != _PAIR_SIZE or pair in seen or pair in visual_pairs:
                continue
            seen.add(pair)
            first = by_name.get(origin)
            second = by_name.get(destination)
            if first is None or second is None:
                continue
            if not _masks_touch(masks[origin], masks[destination], max_gap):
                gaps.append(BoundaryGap(first=first, second=second))

    return gaps


def paises_en_punto(bounds: list[PaisBounds], x: float, y: float) -> list[str]:
    """Países con píxeles visibles bajo el punto, del más arriba al más abajo.

    Returns:
        Nombres de países en orden de z_index descendente.

    """
    hits: list[PaisBounds] = []
    for item in bounds:
        if not (item.left <= x < item.right and item.top <= y < item.bottom):
            continue
        image = _load_image(item.image_path)
        local_x = int(x - item.left)
        local_y = int(y - item.top)
        if (
            0 <= local_x < image.width()
            and 0 <= local_y < image.height()
            and image.pixelColor(local_x, local_y).alpha() >= _ALPHA_THRESHOLD
        ):
            hits.append(item)
    hits.sort(key=lambda item: item.z_index, reverse=True)
    return [item.name for item in hits]
