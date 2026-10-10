"""Genera etiquetas SVG con letras vectoriales desde labels.toml de un tema.

Ejecutar ``QT_QPA_PLATFORM=offscreen python -m scripts.generate_map_labels``.
El SVG resultante no necesita fuentes instaladas para mostrar los nombres.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QGuiApplication,
    QPainterPath,
    QTransform,
)

_ROOT = Path(__file__).resolve().parents[1]
_GLYPH_SIZE = 64


def _number(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def _svg_path(path: QPainterPath) -> str:
    parts: list[str] = []
    index = 0
    while index < path.elementCount():
        element = path.elementAt(index)
        coords = f"{_number(element.x)} {_number(element.y)}"
        if element.isMoveTo():
            parts.append(f"M {coords}")
        elif element.isLineTo():
            parts.append(f"L {coords}")
        elif element.isCurveTo():
            control = path.elementAt(index + 1)
            end = path.elementAt(index + 2)
            parts.append(
                f"C {coords} {_number(control.x)} {_number(control.y)} "
                f"{_number(end.x)} {_number(end.y)}"
            )
            index += 2
        index += 1
    return " ".join(parts)


def _label_path(layout: dict[str, Any], style: dict[str, Any]) -> QPainterPath:
    font = QFont(style["font"])
    font.setPixelSize(_GLYPH_SIZE)
    font.setWeight(QFont.Weight.DemiBold)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    size = layout.get("size", style["font_size"])
    combined = QPainterPath()
    for line_number, line in enumerate(layout["text"].splitlines()):
        glyphs = QPainterPath()
        glyphs.addText(0, 0, font, line)
        bounds = glyphs.boundingRect()
        combined.addPath(
            QTransform()
            .translate(-bounds.center().x(), line_number * _GLYPH_SIZE * 1.25)
            .map(glyphs)
        )
    transform = (
        QTransform()
        .translate(layout["x"], layout["y"])
        .rotate(layout.get("angle", 0))
        .scale(size / _GLYPH_SIZE, size / _GLYPH_SIZE)
    )
    return transform.map(combined)


def _label_svg(
    name: str, layout: dict[str, Any], style: dict[str, Any]
) -> tuple[str, QRectF]:
    glyphs = _label_path(layout, style)
    bounds = glyphs.boundingRect().adjusted(-1, -1, 1, 1)
    ink = escape(style["ink"], {'"': "&quot;"})
    halo = escape(style["halo"], {'"': "&quot;"})
    leader = ""
    anchor = layout.get("anchor")
    if anchor and not bounds.contains(QPointF(*anchor)):
        target = QPointF(*anchor)
        start = QPointF(
            max(bounds.left(), min(target.x(), bounds.right())),
            max(bounds.top(), min(target.y(), bounds.bottom())),
        )
        leader = (
            f'<path d="M {_number(start.x())} {_number(start.y())} '
            f'L {_number(target.x())} {_number(target.y())}" '
            f'fill="none" stroke="{ink}" stroke-width="0.5"/>'
        )
        bounds = bounds.united(QRectF(start, target).normalized())
    path = _svg_path(glyphs)
    text = escape(layout["text"], {'"': "&quot;"})
    return (
        leader + f'<g id="country-label-{name}" aria-label="{text}">'
        f'<path d="{path}" fill="{halo}" stroke="{halo}" '
        'stroke-width="1.3" stroke-linejoin="round"/>'
        f'<path d="{path}" fill="{ink}"/></g>',
        bounds,
    )


def generate(theme: str) -> Path:
    """Escribe el SVG del tema con etiquetas contrastantes y líneas guía.

    Returns:
        Ruta del archivo SVG generado.

    Raises:
        ValueError: Si falta la fuente usada para generar las letras.

    """
    directory = _ROOT / "themes" / theme
    source = tomllib.loads((directory / "labels.toml").read_text(encoding="utf-8"))
    style = source["style"]
    if style["font"] not in QFontDatabase.families():
        message = f"Instalá {style['font']} para generar las etiquetas"
        raise ValueError(message)
    elements: list[str] = []
    bounds = QRectF()
    for name, raw_layout in source["labels"].items():
        element, rect = _label_svg(name, {"text": name, **raw_layout}, style)
        elements.append(element)
        bounds = bounds.united(rect)
    bounds = bounds.adjusted(-2, -2, 2, 2)
    view_box = " ".join(
        _number(value)
        for value in (bounds.x(), bounds.y(), bounds.width(), bounds.height())
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{_number(bounds.width())}" height="{_number(bounds.height())}" '
        f'viewBox="{view_box}">\n' + "\n".join(elements) + "\n</svg>\n"
    )
    output = directory / "labels.svg"
    output.write_text(svg, encoding="utf-8")
    return output


def main() -> int:
    """Genera las etiquetas del mapa indicado.

    Returns:
        Cero después de escribir el SVG.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", default="classic")
    args = parser.parse_args()
    app = QGuiApplication([])
    print(generate(args.theme))
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
