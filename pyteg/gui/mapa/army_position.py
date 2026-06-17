"""Posición del marcador de unidades (círculo verde) sobre el sprite del país."""

from __future__ import annotations

_CIRCLE_SIZE = 16


def resolve_army_position(
    width: int,
    height: int,
    army_x: float,
    army_y: float,
    *,
    circle_size: int = _CIRCLE_SIZE,
) -> tuple[float, float]:
    """Calcula dónde colocar el círculo de unidades dentro del sprite.

    Si ``army_x`` y ``army_y`` son 0, usa el centro del PNG. Siempre clampea
    para que el círculo quede dentro del bounding box del país.

    Returns:
        Coordenadas locales ``(x, y)`` para el ``QGraphicsEllipseItem``.

    """
    if army_x == 0 and army_y == 0:
        x = width / 2 - circle_size / 2
        y = height / 2 - circle_size / 2
    else:
        x = army_x
        y = army_y

    max_x = max(0, width - circle_size)
    max_y = max(0, height - circle_size)
    return max(0.0, min(x, max_x)), max(0.0, min(y, max_y))
