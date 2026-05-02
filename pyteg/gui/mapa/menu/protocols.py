"""Protocolo del host del menú contextual para tipar los mixins."""

from __future__ import annotations

from typing import Any, Protocol


class MenuHost(Protocol):
    """Interfaz mínima que expone la clase `Menu` a los mixins."""

    pais: str
    main_window: Any
    transmisor: Any | None
