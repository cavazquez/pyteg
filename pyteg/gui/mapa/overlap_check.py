"""Detección de superposiciones entre sprites de países del mapa."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QImage

from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

_ALPHA_THRESHOLD = 32


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


def _intersection_area(a: PaisBounds, b: PaisBounds) -> float:
    dx = min(a.right, b.right) - max(a.left, b.left)
    dy = min(a.bottom, b.bottom) - max(a.top, b.top)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def load_pais_bounds(theme: str, *, folder: str = "themes/") -> list[PaisBounds]:
    """Carga posición absoluta y tamaño de cada país desde TOML + PNG.

    Returns:
        Lista de bounds en orden de apilamiento (z_index creciente).

    Raises:
        OSError: Si algún PNG del tema no se puede cargar.

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


def _opaque_at(image: QImage, local_x: int, local_y: int) -> bool:
    if (
        local_x < 0
        or local_y < 0
        or local_x >= image.width()
        or local_y >= image.height()
    ):
        return False
    return image.pixelColor(local_x, local_y).alpha() > _ALPHA_THRESHOLD


def count_opaque_overlap(
    a: PaisBounds, image_a: QImage, b: PaisBounds, image_b: QImage
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
            if _opaque_at(image_a, ax, ay) and _opaque_at(image_b, bx, by):
                count += 1
    return count


def find_pixel_overlaps(
    bounds: list[PaisBounds], *, min_pixels: int = 1
) -> list[PixelOverlap]:
    """Pares con píxeles opacos superpuestos (más preciso que solo bbox).

    Returns:
        Lista ordenada por cantidad de píxeles opacos descendente.

    """
    images = {item.name: QImage(str(item.image_path)) for item in bounds}
    overlaps: list[PixelOverlap] = []

    for i, a in enumerate(bounds):
        for b in bounds[i + 1 :]:
            pixels = count_opaque_overlap(a, images[a.name], b, images[b.name])
            if pixels < min_pixels:
                continue
            top, bottom = (b, a) if b.z_index > a.z_index else (a, b)
            overlaps.append(PixelOverlap(top=top, bottom=bottom, opaque_pixels=pixels))

    overlaps.sort(key=lambda item: item.opaque_pixels, reverse=True)
    return overlaps


def paises_en_punto(bounds: list[PaisBounds], x: float, y: float) -> list[str]:
    """Países cuyo bbox contiene el punto, del más arriba al más abajo.

    Returns:
        Nombres de países en orden de z_index descendente.

    """
    hits = [
        item
        for item in bounds
        if item.left <= x < item.right and item.top <= y < item.bottom
    ]
    hits.sort(key=lambda item: item.z_index, reverse=True)
    return [item.name for item in hits]
