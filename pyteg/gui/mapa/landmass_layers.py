"""Capas visuales generadas desde una partición común del mapa."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsItem

from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsScene

_SHELL_Z = -500.0
_BORDERS_Z = 100.0


def add_landmass_layers(
    scene: QGraphicsScene, theme: str
) -> tuple[list[QGraphicsSvgItem], list[QGraphicsSvgItem]]:
    """Dibuja el bloque terrestre y sus divisiones compartidas una sola vez.

    Los SVG individuales conservan la interacción y los efectos de cada país.
    Los temas sin geometría común siguen usando únicamente sus sprites.

    Returns:
        Capas de masa terrestre y capas de fronteras internas.

    Raises:
        FileNotFoundError: Si falta la capa de fronteras de una masa.
        ValueError: Si un SVG de geometría no se puede cargar.

    """
    directory = Path(get_resource_path(f"themes/{theme}/geometry"))
    if not directory.is_dir():
        return [], []

    shells: list[QGraphicsSvgItem] = []
    borders: list[QGraphicsSvgItem] = []
    for shell_path in sorted(directory.glob("*-shell.svg")):
        manifest_path = shell_path.with_name(
            shell_path.name.replace("-shell.svg", "-manifest.json")
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        origin_x, origin_y = manifest["origin"]
        border_path = shell_path.with_name(
            shell_path.name.replace("-shell.svg", "-borders.svg")
        )
        if not border_path.is_file():
            msg = f"Falta la capa de fronteras para {shell_path}"
            raise FileNotFoundError(msg)
        for path, z_value, items in (
            (shell_path, _SHELL_Z, shells),
            (border_path, _BORDERS_Z, borders),
        ):
            item = QGraphicsSvgItem(str(path))
            renderer = item.renderer()
            if not renderer.isValid():
                msg = f"SVG de geometría inválido: {path}"
                raise ValueError(msg)
            item.setPos(origin_x, origin_y)
            item.setZValue(z_value)
            item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
            scene.addItem(item)
            items.append(item)

    return shells, borders
