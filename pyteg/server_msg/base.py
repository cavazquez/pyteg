"""Mensajes servidor→cliente: interfaz base."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IMsg(ABC):
    """Interfaz base para todos los mensajes del servidor."""

    @abstractmethod
    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje.

        """
