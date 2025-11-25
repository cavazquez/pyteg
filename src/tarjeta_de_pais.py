"""Modelo simple de tarjeta de país con estados de asignación."""

from __future__ import annotations

from typing import Any


class TarjetaDePais:
    """Representa una tarjeta de país con su símbolo y estado de asignación."""

    def __init__(self, pais: str, simbolo: str) -> None:
        """Inicializa una tarjeta de país.

        Args:
            pais: Nombre del país.
            simbolo: Símbolo de la tarjeta (ej: "Galeon", "Globo", "Canon", "Comodin").

        """
        self._pais = pais
        self._simbolo = simbolo
        self._usado = False
        self._jugador: Any = None

    @property
    def pais(self) -> str:
        """Obtiene el nombre del país.

        Returns:
            Nombre del país.

        """
        return self._pais

    @property
    def simbolo(self) -> str:
        """Obtiene el símbolo de la tarjeta.

        Returns:
            Símbolo de la tarjeta.

        """
        return self._simbolo

    def fue_usada(self) -> bool:
        """Verifica si la tarjeta fue usada.

        Returns:
            True si la tarjeta fue usada, False en caso contrario.

        """
        return self._usado

    def jugador(self) -> Any:
        """Obtiene el jugador asignado a la tarjeta.

        Returns:
            Jugador asignado o None si no está asignada.

        """
        return self._jugador

    def asignar(self, jugador: Any) -> None:
        """Asigna la tarjeta a un jugador.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        self._jugador = jugador
        self._usado = True

    def asignada(self) -> bool:
        """Verifica si la tarjeta está asignada a un jugador.

        Returns:
            True si la tarjeta está asignada, False en caso contrario.

        """
        return self._jugador is not None

    def se_puede_asignar(self) -> bool:
        """Verifica si la tarjeta puede ser asignada.

        Returns:
            True si la tarjeta no está asignada y no fue usada.

        """
        return (self._jugador is None) and (self._usado is False)

    def desasignar(self) -> None:
        """Desasigna la tarjeta del jugador actual."""
        self._jugador = None

    def desusar(self) -> None:
        """Marca la tarjeta como no usada."""
        self._usado = False

    def __str__(self) -> str:
        """Retorna representación en string de la tarjeta.

        Returns:
            String con la información de la tarjeta.

        """
        return (
            f"pais: {self._pais}\n simbolo: {self._simbolo}\n"
            f"usado: {self._usado}\n jugador: {self._jugador}"
        )
