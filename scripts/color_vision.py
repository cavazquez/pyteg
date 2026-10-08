"""Simulaciones de visión de color para las capturas de regresión.

Matrices de Machado, Oliveira y Fernandes (severidad 1.0), aplicadas a RGB
lineal. Datos: https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/
CVD_Simulation.html. La aproximación tritan no representa todos los casos.
"""

from __future__ import annotations

from functools import lru_cache
from typing import cast

from PySide6.QtGui import QColor, QImage

COLOR_VISION_MODES = ("normal", "protanopia", "deuteranopia", "tritanopia", "grayscale")
_MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
    "grayscale": ((0.2126, 0.7152, 0.0722),) * 3,
}
_SRGB_THRESHOLD = 0.04045
_LINEAR_THRESHOLD = 0.0031308


@lru_cache(maxsize=65536)
def simulate_rgb(red: int, green: int, blue: int, mode: str) -> tuple[int, ...]:
    """Transforma un píxel sRGB conservando los límites del gamut.

    Returns:
        Tres canales sRGB entre cero y 255.

    Raises:
        ValueError: Si no se reconoce la simulación solicitada.

    """
    if mode == "normal":
        return red, green, blue
    if mode not in _MATRICES:
        message = f"Simulación de color desconocida: {mode}"
        raise ValueError(message)
    channels = [value / 255 for value in (red, green, blue)]
    linear = [
        value / 12.92 if value <= _SRGB_THRESHOLD else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    transformed = [
        max(
            0.0,
            min(
                1.0,
                sum(value * weight for value, weight in zip(linear, row, strict=True)),
            ),
        )
        for row in _MATRICES[mode]
    ]
    return tuple(
        round(
            255
            * (
                value * 12.92
                if value <= _LINEAR_THRESHOLD
                else 1.055 * value ** (1 / 2.4) - 0.055
            )
        )
        for value in transformed
    )


def simulate_color(color: QColor, mode: str) -> QColor:
    """Transforma un color para las comprobaciones de contraste.

    Returns:
        Color simulado con el mismo canal alfa.

    """
    red, green, blue = simulate_rgb(color.red(), color.green(), color.blue(), mode)
    return QColor(red, green, blue, color.alpha())


def simulate_image(image: QImage, mode: str) -> QImage:
    """Genera evidencia visual sin alterar la captura original.

    Returns:
        Copia de la captura con la simulación solicitada.

    """
    result = image.convertToFormat(QImage.Format.Format_RGBA8888)
    pixels = cast("memoryview[int]", result.bits())
    for offset in range(0, len(pixels), 4):
        red, green, blue = simulate_rgb(
            pixels[offset], pixels[offset + 1], pixels[offset + 2], mode
        )
        pixels[offset : offset + 3] = bytes((red, green, blue))
    return result
