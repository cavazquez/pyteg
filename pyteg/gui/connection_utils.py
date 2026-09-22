"""Utilidades compartidas para comprobar conexión del cliente."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


def cliente_esta_conectado(main_window: MainWindowProtocol) -> bool:
    """Indica si el cliente tiene una conexión activa al servidor.

    Returns:
        True si el transmisor reporta conexión activa.

    """
    return bool(main_window.transmisor.esta_conectado())
