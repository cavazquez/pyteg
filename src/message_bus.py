"""Módulo para MessageBus/EventBus del juego.

Este módulo implementa un sistema de mensajería basado en eventos que permite
desacoplar emisores y receptores de mensajes, siguiendo el patrón Observer.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol

from src.logger import get_logger

LOGGER = get_logger("message_bus")


class EventHandler(Protocol):
    """Protocolo para handlers de eventos."""

    def __call__(self, event_data: dict[str, Any]) -> None:
        """Maneja un evento.

        Args:
            event_data: Datos del evento.

        """
        ...


class MessageBus:
    """Bus de mensajes para comunicación desacoplada entre componentes.

    Permite que componentes publiquen eventos y otros se suscriban a ellos
    sin conocer directamente quién los recibe.
    """

    def __init__(self) -> None:
        """Inicializa el bus de mensajes."""
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._enabled = True

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Suscribe un handler a un tipo de evento.

        Args:
            event_type: Tipo de evento al que suscribirse.
            handler: Función o método que manejará el evento.

        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            LOGGER.debug(
                "Handler suscrito a evento '%s' (total: %s)",
                event_type,
                len(self._subscribers[event_type]),
            )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Desuscribe un handler de un tipo de evento.

        Args:
            event_type: Tipo de evento del que desuscribirse.
            handler: Handler a remover.

        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            LOGGER.debug(
                "Handler desuscrito de evento '%s' (total: %s)",
                event_type,
                len(self._subscribers[event_type]),
            )

    def publish(
        self, event_type: str, event_data: dict[str, Any] | None = None
    ) -> None:
        """Publica un evento a todos los suscriptores.

        Args:
            event_type: Tipo de evento a publicar.
            event_data: Datos del evento (opcional).

        """
        if not self._enabled:
            return

        if event_data is None:
            event_data = {}

        handlers = self._subscribers[event_type]
        if not handlers:
            LOGGER.debug("Evento '%s' publicado pero no hay suscriptores", event_type)
            return

        LOGGER.debug(
            "Publicando evento '%s' a %s suscriptor(es)",
            event_type,
            len(handlers),
        )

        for handler in handlers:
            try:
                handler(event_data)
            except Exception:
                LOGGER.exception(
                    "Error al ejecutar handler para evento '%s'",
                    event_type,
                )

    def clear(self) -> None:
        """Limpia todos los suscriptores."""
        self._subscribers.clear()
        LOGGER.debug("Todos los suscriptores han sido removidos")

    def clear_event(self, event_type: str) -> None:
        """Limpia todos los suscriptores de un tipo de evento.

        Args:
            event_type: Tipo de evento a limpiar.

        """
        if event_type in self._subscribers:
            del self._subscribers[event_type]
            LOGGER.debug("Suscriptores del evento '%s' han sido removidos", event_type)

    def disable(self) -> None:
        """Deshabilita el bus (los eventos no se publicarán)."""
        self._enabled = False
        LOGGER.debug("MessageBus deshabilitado")

    def enable(self) -> None:
        """Habilita el bus."""
        self._enabled = True
        LOGGER.debug("MessageBus habilitado")

    def get_subscriber_count(self, event_type: str) -> int:
        """Obtiene la cantidad de suscriptores para un tipo de evento.

        Args:
            event_type: Tipo de evento.

        Returns:
            Cantidad de suscriptores.

        """
        return len(self._subscribers[event_type])


# Instancia global del bus de mensajes
_message_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """Obtiene la instancia global del bus de mensajes.

    Returns:
        Instancia del MessageBus.

    """
    global _message_bus  # noqa: PLW0603
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


def reset_message_bus() -> None:
    """Resetea la instancia global del bus de mensajes (útil para tests)."""
    global _message_bus  # noqa: PLW0603
    _message_bus = None
