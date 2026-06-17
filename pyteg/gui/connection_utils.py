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
    transmisor = main_window.transmisor
    if transmisor is None:
        return False
    if hasattr(transmisor, "esta_conectado"):
        return bool(transmisor.esta_conectado())
    return type(transmisor).__name__ != "ClientNullTransmisor"
