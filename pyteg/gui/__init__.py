"""Paquete principal de la interfaz gráfica del cliente PyTeg.

`from pyteg.gui import Gui` sigue funcionando: la clase vive ahora en
:mod:`pyteg.gui.main_window`. Se expone de forma perezosa con
``__getattr__`` (PEP 562) para evitar disparar la importación pesada de
toda la GUI cuando se accede sólo a sub-paquetes (``pyteg.gui.toolbar``,
``pyteg.gui.tarjetas``, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteg.gui.main_window import Gui

__all__ = ["Gui"]


def __getattr__(name: str) -> Any:
    """Resuelve ``Gui`` perezosamente para evitar imports circulares.

    Args:
        name: Nombre del atributo solicitado en el módulo `pyteg.gui`.

    Returns:
        La clase `Gui` cuando ``name == "Gui"``.

    Raises:
        AttributeError: Para cualquier otro nombre.

    """
    if name == "Gui":
        from pyteg.gui.main_window import Gui  # noqa: PLC0415

        return Gui
    msg = f"module 'pyteg.gui' has no attribute {name!r}"
    raise AttributeError(msg)
