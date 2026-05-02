"""Interfaz base para los mensajes del cliente al servidor."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pyteg.logger import get_logger

LOG = get_logger("client.msg")


class IMsg(ABC):
    """Interfaz base para todos los mensajes del cliente."""

    @abstractmethod
    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje.

        """
