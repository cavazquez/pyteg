"""Procesador de eventos independiente de Qt para clientes y bots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from pyteg.client.state_model import ApplyEventResult, ClientStateModel


class ClientEventProcessor:
    """Aplica eventos al modelo y permite conectar un adaptador de UI."""

    def __init__(
        self,
        model: ClientStateModel | None = None,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Inicializa el procesador sin crear widgets ni acceder a Qt."""
        self.model = model or ClientStateModel()
        self._on_event = on_event

    def process(self, event: dict[str, Any]) -> ApplyEventResult:
        """Aplica un evento y notifica al adaptador opcional.

        Returns:
            Resultado de aplicar el evento al modelo.

        """
        result = self.model.apply_event(event)
        if result.applied and self._on_event is not None:
            self._on_event(event)
        return result
