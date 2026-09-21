"""Renderizado de conexiones visuales declaradas por un tema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene

if TYPE_CHECKING:
    from pyteg.core.mapa.theme_layout import ThemeVisualConnection
    from pyteg.gui.mapa.pais import Pais


_VISUAL_CONNECTION_Z = -1000.0
_VISUAL_CONNECTION_COLOR = QColor("#52758a")
_VISUAL_CONNECTION_WIDTH = 1.5


def add_visual_connections(
    scene: QGraphicsScene,
    connections: list[ThemeVisualConnection],
    countries: dict[str, Pais],
) -> list[QGraphicsPathItem]:
    """Agrega las líneas del tema detrás de los países.

    Los extremos se calculan a partir del centro actual de cada sprite. Los
    puntos intermedios del TOML son coordenadas absolutas de la escena y
    permiten apartar la línea de otros países o formar una polilínea suave.
    Las líneas no aceptan eventos del mouse para no interferir con la selección.

    Returns:
        Elementos gráficos creados para cada conexión.

    """
    items: list[QGraphicsPathItem] = []
    for connection in connections:
        origin = countries[connection.origen]
        destination = countries[connection.destino]
        path = QPainterPath(_country_center(origin))
        for x, y in connection.puntos:
            path.lineTo(QPointF(x, y))
        path.lineTo(_country_center(destination))

        item = QGraphicsPathItem(path)
        pen = QPen(_VISUAL_CONNECTION_COLOR)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidthF(_VISUAL_CONNECTION_WIDTH)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(_VISUAL_CONNECTION_Z)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
        scene.addItem(item)
        items.append(item)
    return items


def _country_center(country: Pais) -> QPointF:
    """Obtiene el centro del sprite en coordenadas de escena.

    Returns:
        Centro del país transformado a coordenadas de escena.

    """
    return country.mapToScene(country.boundingRect().center())


__all__ = ["add_visual_connections"]
