"""Posiciones para placas y cambios de unidades alrededor de una ficha."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtCore import QSizeF
    from PySide6.QtWidgets import QGraphicsItem


def marker_obstacles(
    marker: QGraphicsEllipseItem, overlay: QGraphicsItem
) -> list[QRectF]:
    """Recoge nombres, fichas y placas que el indicador debe dejar visibles.

    Returns:
        Áreas ocupadas en coordenadas de la escena.

    """
    scene = marker.scene()
    obstacles = list(getattr(scene, "country_label_bounds", ()))
    if scene is not None:
        ignored = (marker, overlay, getattr(marker, "_center_text", None))
        for item in scene.items():
            if item in ignored or item.parentItem() is overlay or not item.isVisible():
                continue
            if isinstance(
                item, (QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsTextItem)
            ):
                obstacles.append(item.sceneBoundingRect().adjusted(-1, -1, 1, 1))
    return obstacles


def position_beside_marker(
    marker: QGraphicsEllipseItem,
    size: QSizeF,
    obstacles: Iterable[QRectF],
    *,
    prefer_right: bool = False,
    rise: float = 0,
) -> QPointF:
    """Busca espacio para el indicador y el recorrido de su animación.

    Returns:
        Posición local junto a la ficha con la menor área superpuesta.

    """
    rect = marker.rect()
    width, height = size.width(), size.height()
    below = QPointF(rect.center().x() - width / 2, rect.bottom() + 2)
    right = QPointF(rect.right() + 2, rect.center().y() - height / 2)
    left = QPointF(rect.left() - width - 2, rect.center().y() - height / 2)
    above = QPointF(rect.center().x() - width / 2, rect.top() - height - 2)
    candidates = (
        (right, left, above, below)
        if prefer_right
        else (
            below,
            right,
            left,
            above,
        )
    )
    blocked = tuple(obstacles)

    def overlap_area(position: QPointF) -> float:
        area = 0.0
        path = QRectF(position, size).adjusted(0, -rise, 0, 0)
        candidate = marker.mapRectToScene(path)
        for obstacle in blocked:
            overlap = candidate.intersected(obstacle)
            area += overlap.width() * overlap.height()
        return area

    return min(candidates, key=overlap_area)
