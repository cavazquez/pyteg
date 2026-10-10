"""Capa de nombres vectoriales para temas con un archivo labels.svg."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QGraphicsSvgItem

from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtCore import QRectF
    from PySide6.QtWidgets import QGraphicsScene


def add_country_labels(scene: QGraphicsScene, theme: str) -> QGraphicsSvgItem | None:
    """Agrega nombres encima del mapa sin interceptar clics ni selecciones.

    Returns:
        Capa de etiquetas o None si el tema no usa un archivo independiente.

    Raises:
        ValueError: Si el archivo SVG no se puede cargar.

    """
    path = get_resource_path(f"themes/{theme}/labels.svg")
    if not path.is_file():
        return None
    item = QGraphicsSvgItem(str(path))
    renderer = item.renderer()
    if not renderer.isValid():
        message = f"SVG de etiquetas inválido: {path}"
        raise ValueError(message)
    item.setPos(renderer.viewBoxF().topLeft())
    item.setZValue(500)
    item.setCachingEnabled(False)
    item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
    scene.addItem(item)
    return item


def country_label_bounds(
    layers: Iterable[QGraphicsSvgItem], names: Iterable[str]
) -> list[QRectF]:
    """Obtiene las áreas de los nombres para evitar taparlas con marcadores.

    Returns:
        Rectángulos en coordenadas de la escena, incluidos nombres exteriores.

    """
    countries = tuple(names)
    bounds: list[QRectF] = []
    for layer in layers:
        renderer = layer.renderer()
        origin = renderer.viewBoxF().topLeft()
        for name in countries:
            element = f"country-label-{name}"
            if renderer.elementExists(element):
                rect = renderer.boundsOnElement(element).translated(-origin)
                bounds.append(layer.mapRectToScene(rect).adjusted(-1, -1, 1, 1))
    return bounds
