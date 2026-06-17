"""Reporta superposiciones entre sprites de países en un tema de mapa.

Uso:
    uv run python scripts/check_map_overlaps.py
    uv run python scripts/check_map_overlaps.py --theme classic --pixels
"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.mapa.overlap_check import (
    find_bbox_overlaps,
    find_pixel_overlaps,
    load_pais_bounds,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detecta países superpuestos en el layout del mapa (TOML + PNG)."
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
    return parser.parse_args()


def main() -> int:
    """Ejecuta el análisis e imprime pares superpuestos.

    Returns:
        0 si no hay solapamientos de bbox; 1 si los hay.

    """
    args = _parse_args()
    _app = QApplication(sys.argv)

    bounds = load_pais_bounds(args.theme)
    bbox_overlaps = find_bbox_overlaps(bounds)

    print(f"Tema: {args.theme} ({len(bounds)} países)\n")

    if not bbox_overlaps:
        print("Sin superposiciones de bounding box.")
        return 0

    print(f"=== Bounding boxes ({len(bbox_overlaps)} pares) ===")
    for overlap in bbox_overlaps:
        print(
            f"  {overlap.top.name} encima de {overlap.bottom.name} "
            f"— área bbox {overlap.area:.0f} px² "
            f"({overlap.top.continent} / {overlap.bottom.continent})"
        )

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
    return 1 if bbox_overlaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
