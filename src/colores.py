"""Módulo para manejar colores RGB en el juego."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from src.config import HEX_COLOR_LENGTH, RGB_MAX_VALUE


class IColor(ABC):
    """Interfaz abstracta para representar colores RGB."""

    _r: int
    _g: int
    _b: int

    @abstractmethod
    def __init__(self, r: int, g: int, b: int) -> None:
        """Inicializa un color con valores RGB.

        Args:
            r: Componente rojo (0-255).
            g: Componente verde (0-255).
            b: Componente azul (0-255).

        """
        self._validate_rgb(r, g, b)
        self._r = r
        self._g = g
        self._b = b

    def to_json(self) -> str:
        """Convierte el color a formato JSON.

        Returns:
            String JSON con los valores RGB.

        """
        return json.dumps({"r": self._r, "g": self._g, "b": self._b})

    def __str__(self) -> str:
        """Retorna representación en string del color.

        Returns:
            String con los valores RGB.

        """
        return f"r: {self._r}, g: {self._g}, b: {self._b}"

    def to_hex(self) -> str:
        """Convierte el color a formato hexadecimal.

        Returns:
            String hexadecimal del color (ej: #ff0000).

        """
        return "".join(["#", ("{:02X}" * 3).format(self._r, self._g, self._b).lower()])

    def __eq__(self, otro: object) -> bool:
        """Compara dos colores por igualdad.

        Args:
            otro: Otro objeto a comparar.

        Returns:
            True si los colores son iguales, False en caso contrario.

        """
        if not isinstance(otro, IColor):
            return NotImplemented
        return self._r == otro._r and self._g == otro._g and self._b == otro._b

    def __hash__(self) -> int:
        """Retorna el hash del color.

        Returns:
            Hash del color basado en su valor hexadecimal.

        """
        return hash(self.to_hex())

    @staticmethod
    def _validate_rgb(r: int, g: int, b: int) -> None:
        if not all(isinstance(v, int) and 0 <= v <= RGB_MAX_VALUE for v in (r, g, b)):
            msg = f"Los valores RGB deben ser enteros entre 0 y {RGB_MAX_VALUE}"
            raise ValueError(msg)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> IColor:
        """Crea un color desde valores RGB.

        Args:
            r: Componente rojo (0-255).
            g: Componente verde (0-255).
            b: Componente azul (0-255).

        Returns:
            Instancia del color.

        """
        return cls(r, g, b)

    @classmethod
    def from_hex(cls, hex_value: str) -> IColor:
        """Crea un color desde un valor hexadecimal.

        Args:
            hex_value: Valor hexadecimal (ej: "#FF0000" o "FF0000").

        Returns:
            Instancia del color.

        Raises:
            ValueError: Si el valor hexadecimal no tiene 6 caracteres.

        """
        hex_value = hex_value.lstrip("#")
        if len(hex_value) != HEX_COLOR_LENGTH:
            msg = f"El valor hexadecimal debe tener {HEX_COLOR_LENGTH} caracteres"
            raise ValueError(msg)
        r, g, b = tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
        return cls(r, g, b)


class Rojo(IColor):
    """Color rojo (RGB: 255, 0, 0)."""

    def __init__(self) -> None:
        """Inicializa el color rojo."""
        super().__init__(255, 0, 0)


class Verde(IColor):
    """Color verde (RGB: 0, 255, 0)."""

    def __init__(self) -> None:
        """Inicializa el color verde."""
        super().__init__(0, 255, 0)


class Azul(IColor):
    """Color azul (RGB: 0, 0, 255)."""

    def __init__(self) -> None:
        """Inicializa el color azul."""
        super().__init__(0, 0, 255)


class Amarillo(IColor):
    """Color amarillo (RGB: 255, 255, 0)."""

    def __init__(self) -> None:
        """Inicializa el color amarillo."""
        super().__init__(255, 255, 0)


class Cian(IColor):
    """Color cian (RGB: 0, 255, 255)."""

    def __init__(self) -> None:
        """Inicializa el color cian."""
        super().__init__(0, 255, 255)


class Magenta(IColor):
    """Color magenta (RGB: 255, 0, 255)."""

    def __init__(self) -> None:
        """Inicializa el color magenta."""
        super().__init__(255, 0, 255)


class Negro(IColor):
    """Color negro (RGB: 0, 0, 0)."""

    def __init__(self) -> None:
        """Inicializa el color negro."""
        super().__init__(0, 0, 0)


class Blanco(IColor):
    """Color blanco (RGB: 255, 255, 255)."""

    def __init__(self) -> None:
        """Inicializa el color blanco."""
        super().__init__(255, 255, 255)
