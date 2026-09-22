"""Capturas offscreen y chequeos estructurales del mapa para CI.

El smoke no depende de una pantalla real: abre cada tema con Qt offscreen,
renderiza tres tamaños habituales y deja PNG + manifest como artefactos de
revisión cuando cambia el mapa o falla el workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.gui.widgets.view import QCustomGraphicsView

DEFAULT_SIZES = ((1024, 600), (1280, 800), (1920, 1080))
_MIN_CAPTURE_WIDTH = 640
_MIN_CAPTURE_HEIGHT = 400


@dataclass(frozen=True)
class CaptureRecord:
    """Datos verificables asociados a una captura."""

    theme: str
    width: int
    height: int
    countries: int
    visual_connections: int
    scene_left: float
    scene_top: float
    scene_width: float
    scene_height: float
    output: str


def _parse_size(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except TypeError, ValueError:
        message = "el tamaño debe tener formato ANCHOxALTO"
        raise argparse.ArgumentTypeError(message) from None
    if width < _MIN_CAPTURE_WIDTH or height < _MIN_CAPTURE_HEIGHT:
        message = "el tamaño es demasiado pequeño para el mapa"
        raise argparse.ArgumentTypeError(message)
    return width, height


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--themes",
        nargs="+",
        default=[DEFAULT_MAP_THEME, "test"],
        help="Temas a renderizar (default: classic test)",
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=_parse_size,
        default=list(DEFAULT_SIZES),
        help="Tamaños ANCHOxALTO (default: 1024x600 1280x800 1920x1080)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/map-visual"),
        help="Directorio para PNG y manifest",
    )
    return parser.parse_args()


def render_capture(
    app: QApplication,
    theme: str,
    size: tuple[int, int],
    output_dir: Path,
) -> CaptureRecord:
    """Renderiza un tema a una imagen y valida sus bounds básicos.

    Returns:
        Metadatos de la captura generada.

    Raises:
        OSError: Si la imagen no se puede guardar.
        RuntimeError: Si el tema no tiene contenido o queda fuera de bounds.

    """
    width, height = size
    host = SimpleNamespace(
        scene=None,
        update_status_bar=lambda *_args: None,
        clear_status_bar=lambda: None,
    )
    scene = QCustomGraphicsScene(host, theme=theme)
    host.scene = scene
    view = QCustomGraphicsView(scene, host)
    view.resize(QSize(width, height))
    view.show()
    app.processEvents()

    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    view.render(painter)
    painter.end()

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{theme}-{width}x{height}.png"
    if not image.save(str(output), "PNG"):  # type: ignore[call-overload]
        message = f"no se pudo guardar la captura {output}"
        raise OSError(message)

    bounds = scene.itemsBoundingRect()
    scene_rect = scene.sceneRect()
    if bounds.isEmpty() or bounds.width() <= 0 or bounds.height() <= 0:
        message = f"el tema {theme} no tiene contenido visible"
        raise RuntimeError(message)
    if not scene_rect.contains(bounds):
        message = (
            f"el tema {theme} tiene elementos fuera de sceneRect: "
            f"{bounds} no está contenido en {scene_rect}"
        )
        raise RuntimeError(message)
    if not scene.paises:
        message = f"el tema {theme} no cargó países"
        raise RuntimeError(message)
    if theme == DEFAULT_MAP_THEME and len(scene.visual_connections) == 0:
        message = "el tema clásico no cargó conexiones visuales"
        raise RuntimeError(message)

    view.close()
    return CaptureRecord(
        theme=theme,
        width=width,
        height=height,
        countries=len(scene.paises),
        visual_connections=len(scene.visual_connections),
        scene_left=scene_rect.left(),
        scene_top=scene_rect.top(),
        scene_width=scene_rect.width(),
        scene_height=scene_rect.height(),
        output=str(output),
    )


def main() -> int:
    """Ejecuta todas las capturas y escribe el manifest.

    Returns:
        Código de salida cero si todas las capturas pasan.

    """
    args = _parse_args()
    app = cast("QApplication", QApplication.instance() or QApplication(sys.argv))
    records = [
        render_capture(app, theme, size, args.output_dir)
        for theme in args.themes
        for size in args.sizes
    ]
    manifest = args.output_dir / "manifest.json"
    manifest.write_text(
        json.dumps([asdict(record) for record in records], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Capturas visuales: {len(records)} ({manifest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
