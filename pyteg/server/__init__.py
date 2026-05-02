"""Paquete principal del servidor PyTeg.

`from pyteg.server import Server` y el entry point `pyteg.server:main`
siguen funcionando vía `__getattr__` (PEP 562) sobre :mod:`pyteg.server.app`.
Esto evita disparar la importación pesada del servidor al acceder a
sub-paquetes (`pyteg.server.msg`, `pyteg.server.tasks`, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteg.server.app import Server, main, parse_arguments

__all__ = ["Server", "main", "parse_arguments"]


def __getattr__(name: str) -> Any:
    """Resuelve atributos de `pyteg.server.app` perezosamente.

    Args:
        name: Nombre del atributo solicitado en el módulo `pyteg.server`.

    Returns:
        El símbolo correspondiente de :mod:`pyteg.server.app`.

    Raises:
        AttributeError: Si el nombre no existe en `app`.

    """
    if name in {"Server", "main", "parse_arguments"}:
        from pyteg.server import app  # noqa: PLC0415

        return getattr(app, name)
    msg = f"module 'pyteg.server' has no attribute {name!r}"
    raise AttributeError(msg)
