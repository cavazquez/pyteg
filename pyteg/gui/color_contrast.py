"""Contraste de colores sRGB para indicadores y verificaciones visuales."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtGui import QColor

_SRGB_THRESHOLD = 0.04045


def relative_luminance(color: QColor) -> float:
    """Calcula la luminancia relativa de un color sRGB.

    Returns:
        Luminancia lineal entre cero y uno.

    """
    channels = (color.redF(), color.greenF(), color.blueF())
    linear = [
        value / 12.92 if value <= _SRGB_THRESHOLD else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return sum(
        value * weight
        for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
    )


def contrast_ratio(first: QColor, second: QColor) -> float:
    """Calcula el contraste entre dos colores opacos.

    Returns:
        Relación entre uno y veintiuno.

    """
    low, high = sorted((relative_luminance(first), relative_luminance(second)))
    return (high + 0.05) / (low + 0.05)
