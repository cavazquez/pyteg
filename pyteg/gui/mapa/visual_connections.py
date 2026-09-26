"""Renderizado de conexiones visuales declaradas por un tema."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import starmap
from math import ceil, hypot
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene

if TYPE_CHECKING:
    from pyteg.core.mapa.theme_layout import ThemeVisualConnection
    from pyteg.gui.mapa.pais import Pais


_VISUAL_CONNECTION_Z = -1000.0
_REVANCHA_CONNECTION_Z = -400.0
_VISUAL_CONNECTION_COLOR = QColor(30, 78, 101, 225)
_VISUAL_CONNECTION_WIDTH = 2.0
_REVANCHA_CONNECTION_COLOR = QColor("#c48a3c")
_REVANCHA_CONNECTION_WIDTH = 3.4
_HINT_CONNECTION_COLOR = QColor("#b45b12")
_HINT_CONNECTION_WIDTH = 2.8
_HINT_CONNECTION_Z = 85.0
_BOUNDARY_SAMPLE_STEP = 0.5
_BOUNDARY_REFINEMENTS = 10


@dataclass(frozen=True, slots=True)
class _ConnectionStyle:
    color: QColor
    width: float
    pen_style: Qt.PenStyle
    z: float


def _connection_style(theme: str, *, highlight: bool = False) -> _ConnectionStyle:
    if highlight:
        return _ConnectionStyle(
            _HINT_CONNECTION_COLOR,
            _HINT_CONNECTION_WIDTH,
            Qt.PenStyle.DashLine,
            _HINT_CONNECTION_Z,
        )
    if theme == "revancha":
        return _ConnectionStyle(
            _REVANCHA_CONNECTION_COLOR,
            _REVANCHA_CONNECTION_WIDTH,
            Qt.PenStyle.SolidLine,
            _REVANCHA_CONNECTION_Z,
        )
    return _ConnectionStyle(
        _VISUAL_CONNECTION_COLOR,
        _VISUAL_CONNECTION_WIDTH,
        Qt.PenStyle.DashLine,
        _VISUAL_CONNECTION_Z,
    )


def add_visual_connections(  # noqa: PLR0914
    scene: QGraphicsScene,
    connections: list[ThemeVisualConnection],
    countries: dict[str, Pais],
    *,
    theme: str = "classic",
    highlight: bool = False,
) -> list[QGraphicsPathItem]:
    """Agrega las líneas del tema detrás de los países.

    Los extremos se recortan contra el contorno de cada país en la dirección
    del siguiente punto de ruta. Los puntos intermedios son coordenadas
    absolutas de escena. Con
    ``envolver=horizontal``, los dos puntos son la salida por la izquierda y
    la reentrada por la derecha; no se traza el segmento intermedio.

    Returns:
        Elementos gráficos creados para cada conexión.

    """
    items: list[QGraphicsPathItem] = []
    style = _connection_style(theme, highlight=highlight)
    for connection in connections:
        origin = countries[connection.origen]
        destination = countries[connection.destino]
        use_marker_center = theme == "revancha"
        origin_center = _country_center(origin, use_marker=use_marker_center)
        destination_center = _country_center(destination, use_marker=use_marker_center)
        if connection.envolver == "horizontal":
            exit_point, entry_point = connection.puntos
            origin_target = _first_outside(
                origin, [QPointF(*exit_point)], destination_center
            )
            destination_target = _first_outside(
                destination, [QPointF(*entry_point)], origin_center
            )
            origin_anchor = _boundary_anchor(origin, origin_target, origin_center)
            destination_anchor = _boundary_anchor(
                destination, destination_target, destination_center
            )
            path = QPainterPath(origin_anchor)
            path.lineTo(QPointF(*exit_point))
            path.moveTo(QPointF(*entry_point))
            path.lineTo(destination_anchor)
        else:
            waypoints = list(starmap(QPointF, connection.puntos))
            origin_shape = origin.shape()
            destination_shape = destination.shape()
            while waypoints and origin_shape.contains(
                origin.mapFromScene(waypoints[0])
            ):
                waypoints.pop(0)
            while waypoints and destination_shape.contains(
                destination.mapFromScene(waypoints[-1])
            ):
                waypoints.pop()
            origin_target = _first_outside(origin, waypoints, destination_center)
            destination_target = _first_outside(
                destination, list(reversed(waypoints)), origin_center
            )
            origin_anchor = _boundary_anchor(origin, origin_target, origin_center)
            destination_anchor = _boundary_anchor(
                destination, destination_target, destination_center
            )
            path = QPainterPath(origin_anchor)
            for waypoint in waypoints:
                path.lineTo(waypoint)
            path.lineTo(destination_anchor)

        item = QGraphicsPathItem(path)
        pen = QPen(style.color)
        pen.setStyle(style.pen_style)
        pen.setWidthF(style.width)
        pen.setCosmetic(True)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        item.setPen(pen)
        item.setZValue(style.z)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
        if highlight:
            item.setToolTip(
                f"Conexión jugable: {connection.origen} ↔ {connection.destino}"
            )
        if connection.envolver == "horizontal":
            _add_wrap_arrowheads(item, exit_point, entry_point, style.color)
        scene.addItem(item)
        items.append(item)
    return items


def _add_wrap_arrowheads(
    route: QGraphicsPathItem,
    exit_point: tuple[float, float],
    entry_point: tuple[float, float],
    color: QColor,
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
        arrow.setBrush(QBrush(color))
        arrow.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        arrow.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)


def _country_center(country: Pais, *, use_marker: bool = False) -> QPointF:
    """Obtiene el centro del sprite en coordenadas de escena.

    Returns:
        Centro del país transformado a coordenadas de escena.

    """
    if use_marker:
        return country.mapToScene(
            QPointF(country._army_x + 8, country._army_y + 8)  # noqa: SLF001
        )
    return country.mapToScene(country.boundingRect().center())


def _boundary_anchor(  # noqa: PLR0914
    country: Pais, target: QPointF, center: QPointF | None = None
) -> QPointF:
    """Intersects the ray toward ``target`` with the country's visible edge.

    Returns:
        A scene point on the last boundary crossing before the target.

    """
    center = _country_center(country) if center is None else center
    local_center = country.mapFromScene(center)
    local_target = country.mapFromScene(target)
    delta_x = local_target.x() - local_center.x()
    delta_y = local_target.y() - local_center.y()
    distance = hypot(delta_x, delta_y)
    if distance == 0:
        return center

    shape = country.shape()
    steps = max(1, ceil(distance / _BOUNDARY_SAMPLE_STEP))
    last_inside: float | None = 0.0 if shape.contains(local_center) else None
    crossing: tuple[float, float] | None = None
    for index in range(1, steps + 1):
        position = index / steps
        point = QPointF(
            local_center.x() + delta_x * position,
            local_center.y() + delta_y * position,
        )
        if shape.contains(point):
            last_inside = position
        elif last_inside is not None:
            crossing = (last_inside, position)

    if crossing is None:
        return center

    inside, outside = crossing
    for _ in range(_BOUNDARY_REFINEMENTS):
        midpoint = (inside + outside) / 2
        point = QPointF(
            local_center.x() + delta_x * midpoint,
            local_center.y() + delta_y * midpoint,
        )
        if shape.contains(point):
            inside = midpoint
        else:
            outside = midpoint

    anchor = QPointF(
        local_center.x() + delta_x * outside,
        local_center.y() + delta_y * outside,
    )
    return country.mapToScene(anchor)


def _first_outside(country: Pais, targets: list[QPointF], fallback: QPointF) -> QPointF:
    """Choose the first route point outside a country's visible silhouette.

    Returns:
        The first outside target, or ``fallback`` if none is outside.

    """
    shape = country.shape()
    return next(
        (
            target
            for target in targets
            if not shape.contains(country.mapFromScene(target))
        ),
        fallback,
    )


__all__ = ["add_visual_connections"]
