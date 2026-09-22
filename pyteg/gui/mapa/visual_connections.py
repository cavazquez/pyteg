"""Renderizado de conexiones visuales declaradas por un tema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene

if TYPE_CHECKING:
    from pyteg.core.mapa.theme_layout import ThemeVisualConnection
    from pyteg.gui.mapa.pais import Pais


_VISUAL_CONNECTION_Z = -1000.0
_VISUAL_CONNECTION_COLOR = QColor(30, 78, 101, 225)
_VISUAL_CONNECTION_WIDTH = 2.0


def add_visual_connections(
    scene: QGraphicsScene,
    connections: list[ThemeVisualConnection],
    countries: dict[str, Pais],
) -> list[QGraphicsPathItem]:
    """Agrega las líneas del tema detrás de los países.

    Los extremos se calculan a partir del centro actual de cada sprite. Los
    puntos intermedios son coordenadas absolutas de escena. Con
    ``envolver=horizontal``, los dos puntos son la salida por la izquierda y
    la reentrada por la derecha; no se traza el segmento intermedio.

    Returns:
        Elementos gráficos creados para cada conexión.

    """
    items: list[QGraphicsPathItem] = []
    for connection in connections:
        origin = countries[connection.origen]
        destination = countries[connection.destino]
        path = QPainterPath(_country_center(origin))
        if connection.envolver == "horizontal":
            exit_point, entry_point = connection.puntos
            path.lineTo(QPointF(*exit_point))
            path.moveTo(QPointF(*entry_point))
            path.lineTo(_country_center(destination))
        else:
            for x, y in connection.puntos:
                path.lineTo(QPointF(x, y))
            path.lineTo(_country_center(destination))

        item = QGraphicsPathItem(path)
        pen = QPen(_VISUAL_CONNECTION_COLOR)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidthF(_VISUAL_CONNECTION_WIDTH)
        pen.setCosmetic(True)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        item.setPen(pen)
        item.setZValue(_VISUAL_CONNECTION_Z)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
        if connection.envolver == "horizontal":
            _add_wrap_arrowheads(item, exit_point, entry_point)
        scene.addItem(item)
        items.append(item)
    return items


def _add_wrap_arrowheads(
    route: QGraphicsPathItem,
    exit_point: tuple[float, float],
    entry_point: tuple[float, float],
) -> None:
    arrow_specs = (
        (exit_point[0], exit_point[0] + 6.0, exit_point[1]),
        (entry_point[0] - 6.0, entry_point[0], entry_point[1]),
    )
    for tip_x, base_x, y in arrow_specs:
        arrow_path = QPainterPath(QPointF(tip_x, y))
        arrow_path.lineTo(QPointF(base_x, y - 3.0))
        arrow_path.lineTo(QPointF(base_x, y + 3.0))
        arrow_path.closeSubpath()

        arrow = QGraphicsPathItem(arrow_path, route)
        arrow.setPen(QPen(Qt.PenStyle.NoPen))
        arrow.setBrush(QBrush(_VISUAL_CONNECTION_COLOR))
        arrow.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        arrow.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)


def _country_center(country: Pais) -> QPointF:
    """Obtiene el centro del sprite en coordenadas de escena.

    Returns:
        Centro del país transformado a coordenadas de escena.

    """
    return country.mapToScene(country.boundingRect().center())


__all__ = ["add_visual_connections"]
