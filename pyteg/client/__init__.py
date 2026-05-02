"""Paquete principal del cliente PyTeg.

`from pyteg.client import Client` sigue funcionando vía `__getattr__`
(PEP 562) sobre :mod:`pyteg.client.app`. Esto evita disparar la
importación pesada del cliente al acceder a sub-paquetes
(`pyteg.client.tasks`, `pyteg.client.conexion`, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteg.client.app import Client

__all__ = ["Client"]


def __getattr__(name: str) -> Any:
    """Resuelve atributos de `pyteg.client.app` perezosamente.

    Args:
        name: Nombre del atributo solicitado en el módulo `pyteg.client`.

    Returns:
        El símbolo correspondiente de :mod:`pyteg.client.app`.

    Raises:
        AttributeError: Si el nombre no existe en `app`.

    """
    if name == "Client":
        from pyteg.client import app  # noqa: PLC0415

        return app.Client
    msg = f"module 'pyteg.client' has no attribute {name!r}"
    raise AttributeError(msg)
