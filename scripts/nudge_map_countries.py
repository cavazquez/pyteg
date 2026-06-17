"""Aplica separación suave a países superpuestos en un tema de mapa."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.mapa.layout_nudge import (
    apply_continent_offsets_to_paises_toml,
    apply_positions_to_paises_toml,
    compute_nudged_positions,
    spread_continent_offsets,
)
from pyteg.gui.mapa.overlap_check import find_pixel_overlaps, load_pais_bounds


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Separa países superpuestos en paises.toml"
    )
    parser.add_argument("--theme", default=DEFAULT_MAP_THEME)
    parser.add_argument("--step", type=float, default=2.0, help="Píxeles por iteración")
    parser.add_argument("--iterations", type=int, default=6)
    parser.add_argument("--min-pixels", type=int, default=180)
    parser.add_argument(
        "--spread-continents",
        type=int,
        default=8,
        help="Separación extra entre bloques de continente (0 = no tocar)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar métricas")
    return parser.parse_args()


def _count_overlaps(theme: str, min_pixels: int) -> int:
    bounds = load_pais_bounds(theme)
    return len(find_pixel_overlaps(bounds, min_pixels=min_pixels))


def main() -> int:
    """Nudge de layout y reporte antes/después.

    Returns:
        0 si se aplicó o fue dry-run; 1 si no hubo cambios.

    """
    args = _parse_args()
    _app = QApplication(sys.argv)

    before = _count_overlaps(args.theme, args.min_pixels)
    positions = compute_nudged_positions(
        args.theme,
        step=args.step,
        iterations=args.iterations,
        min_pixels=args.min_pixels,
    )

    print(f"Tema: {args.theme}")
    print(f"Superposiciones opacas (>={args.min_pixels}px) antes: {before}")

    if args.dry_run:
        print("Dry-run: no se modificó paises.toml")
        return 0

    apply_positions_to_paises_toml(args.theme, positions)
    if args.spread_continents > 0:
        offsets = spread_continent_offsets(args.theme, gap=args.spread_continents)
        apply_continent_offsets_to_paises_toml(args.theme, offsets)

    after = _count_overlaps(args.theme, args.min_pixels)
    print(f"Superposiciones opacas después: {after}")
    print(f"Actualizado themes/{args.theme}/paises.toml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
