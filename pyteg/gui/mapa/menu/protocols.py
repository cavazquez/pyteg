"""Protocolo del host del menú contextual para tipar los mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pyteg.client.conexion.transmisor.protocol import IClientTransmisor


class MenuHost(Protocol):
    """Interfaz mínima que expone la clase `Menu` a los mixins."""

    pais: str | None
    continente_mapa: str | None
    main_window: Any
    transmisor: IClientTransmisor
