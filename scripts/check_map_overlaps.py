"""Reporta superposiciones entre sprites de países en un tema de mapa.

Uso:
    uv run python scripts/check_map_overlaps.py
    uv run python scripts/check_map_overlaps.py --theme classic --pixels
    uv run python scripts/check_map_overlaps.py --max-bbox-pairs 75
    uv run python scripts/check_map_overlaps.py --theme classic --strict-boundaries
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.mapa.overlap_check import (
    BboxOverlap,
    PaisBounds,
    find_bbox_overlaps,
    find_pixel_overlaps,
    find_solid_overlaps,
    find_unconnected_boundaries,
    load_pais_bounds,
)
from pyteg.toml_reader import TomlReader

if TYPE_CHECKING:
    from collections.abc import Sequence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Detecta países superpuestos en el layout del mapa (TOML + SVG/PNG)."
        )
    )
    parser.add_argument(
        "--theme",
        default=DEFAULT_MAP_THEME,
        help=f"Tema en themes/ (default: {DEFAULT_MAP_THEME})",
    )
    parser.add_argument(
        "--pixels",
        action="store_true",
        help="Además del bbox, contar píxeles opacos superpuestos (más lento)",
    )
    parser.add_argument(
        "--min-pixels",
        type=int,
        default=50,
        help="Umbral mínimo de píxeles opacos para reportar (default: 50)",
    )
    parser.add_argument(
        "--max-bbox-pairs",
        type=int,
        default=None,
        help="Falla si hay más pares bbox superpuestos que este valor",
    )
    parser.add_argument(
        "--fail-on-cross-continent",
        action="store_true",
        help="Falla si hay solapamientos bbox entre continentes distintos",
    )
    parser.add_argument(
        "--strict-boundaries",
        action="store_true",
        help=(
            "Falla si los interiores sólidos se solapan o si una frontera "
            "terrestre declarada queda separada"
        ),
    )
    parser.add_argument(
        "--max-contact-gap",
        type=int,
        default=1,
        help="Tolerancia de contacto para fronteras terrestres (default: 1)",
    )
    parser.add_argument(
        "--allow-cross",
        default="",
        help="Pares continente cruzado permitidos, ej. Groenlandia:Islandia",
    )
    return parser.parse_args()


def _check_cross_continent(
    bbox_overlaps: Sequence[BboxOverlap], allow_cross: str
) -> int:
    allowed = {
        tuple(pair.split(":", 1)) for pair in allow_cross.split(",") if ":" in pair
    }
    cross = [
        overlap
        for overlap in bbox_overlaps
        if overlap.top.continent != overlap.bottom.continent
        and (overlap.top.name, overlap.bottom.name) not in allowed
        and (overlap.bottom.name, overlap.top.name) not in allowed
    ]
    if not cross:
        return 0
    print(f"\nERROR: {len(cross)} solapamientos entre continentes distintos")
    return 1


def _check_strict_boundaries(
    bounds: list[PaisBounds],
    reader: TomlReader,
    max_contact_gap: int,
) -> int:
    exit_code = 0
    solid_overlaps = find_solid_overlaps(bounds, min_pixels=1)
    if solid_overlaps:
        print(
            "\n=== Solapamientos sólidos (deben ser cero) "
            f"({len(solid_overlaps)} pares) ==="
        )
        for overlap in solid_overlaps:
            print(
                f"  {overlap.top.name}/{overlap.bottom.name} — "
                f"{overlap.opaque_pixels} px"
            )
        exit_code = 1

    visual_connections = [
        (connection.origen, connection.destino)
        for connection in reader.get_conexiones_visuales()
    ]
    gaps = find_unconnected_boundaries(
        bounds,
        reader.adyacencias,
        visual_connections,
        max_gap=max_contact_gap,
    )
    if gaps:
        print(
            "\n=== Fronteras terrestres separadas "
            f"(>{max_contact_gap} px) ({len(gaps)} pares) ==="
        )
        for gap in gaps:
            print(f"  {gap.first.name}/{gap.second.name}")
        exit_code = 1
    return exit_code


def main() -> int:
    """Ejecuta el análisis e imprime pares superpuestos.

    Returns:
        0 si pasa los umbrales; 1 si hay violaciones.

    """
    args = _parse_args()
    _app = QApplication(sys.argv)

    bounds = load_pais_bounds(args.theme)
    bbox_overlaps = find_bbox_overlaps(bounds)

    print(f"Tema: {args.theme} ({len(bounds)} países)\n")

    if not bbox_overlaps and not args.strict_boundaries:
        print("Sin superposiciones de bounding box.")
        return 0

    if bbox_overlaps:
        print(f"=== Bounding boxes ({len(bbox_overlaps)} pares) ===")
        for overlap in bbox_overlaps:
            print(
                f"  {overlap.top.name} encima de {overlap.bottom.name} "
                f"— área bbox {overlap.area:.0f} px² "
                f"({overlap.top.continent} / {overlap.bottom.continent})"
            )
    else:
        print("Sin superposiciones de bounding box.")

    if args.pixels:
        print(f"\n=== Píxeles opacos (umbral >= {args.min_pixels}) ===")
        pixel_overlaps = find_pixel_overlaps(bounds, min_pixels=args.min_pixels)
        if not pixel_overlaps:
            print("  Sin solapamiento visible (solo transparencia en bbox).")
        else:
            for pixel_overlap in pixel_overlaps:
                print(
                    f"  {pixel_overlap.top.name} encima de {pixel_overlap.bottom.name} "
                    f"— {pixel_overlap.opaque_pixels} px opacos"
                )

    print(
        "\nTip: en la GUI, mantené Shift y mové el mouse para ver "
        "la pila de países bajo el cursor."
    )

    exit_code = 0
    if args.max_bbox_pairs is not None and len(bbox_overlaps) > args.max_bbox_pairs:
        print(
            f"\nERROR: {len(bbox_overlaps)} pares bbox > máximo {args.max_bbox_pairs}"
        )
        exit_code = 1

    if args.fail_on_cross_continent:
        exit_code = max(
            exit_code,
            _check_cross_continent(bbox_overlaps, args.allow_cross),
        )

    if args.strict_boundaries:
        reader = TomlReader.from_theme(args.theme, strict=True)
        exit_code = max(
            exit_code,
            _check_strict_boundaries(bounds, reader, args.max_contact_gap),
        )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
