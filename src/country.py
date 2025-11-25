"""Representación sencilla de un país."""

from __future__ import annotations


class Country:
    """Representa un país con su nombre."""

    def __init__(self, name: str) -> None:
        """Inicializa el país con un nombre.

        Args:
            name: Nombre del país.

        """
        self._name = name

    def get_name(self) -> str:
        """Obtiene el nombre del país.

        Returns:
            Nombre del país.

        """
        return self._name
