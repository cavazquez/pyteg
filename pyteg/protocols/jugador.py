"""Protocolo mínimo de jugador del dominio (`IJugador`).

Permite tipar dueños de país, dueños de tarjeta y participantes de canjes
sin importar `Client` (servidor) ni clases de tests; la identidad canónica
es siempre `userid` (int) — ver `docs/DECISIONS.md` (ADR-012).
"""

from __future__ import annotations

from typing import Protocol


class IJugador(Protocol):
    """Interfaz mínima para entidades que representan un jugador."""

    def userid(self) -> int:
        """Devuelve el `userid` (int) del jugador.

        Returns:
            Identificador entero único del jugador.

        """
        ...

    def username(self) -> str:
        """Devuelve el nombre de usuario del jugador.

        Returns:
            Nombre legible del jugador (UI/chat).

        """
        ...
