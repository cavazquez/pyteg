"""Adaptador del motor: hospedar y persistir sólo dependen de este puerto."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.server.app import Server

if TYPE_CHECKING:
    from collections.abc import Callable


class RecoveryEngine(Protocol):
    """Contrato que necesita un anfitrión para crear y restaurar motores."""

    def create(self, theme: str, rules_profile: str | None = None) -> Server:
        """Crea un motor con reglas y mapa independientes."""
        ...

    def restore(self, checkpoint: dict[str, Any]) -> Server:
        """Construye otro motor desde un memento."""
        ...

    def capture(self, server: Server) -> dict[str, Any]:
        """Captura el motor en su serializador."""
        ...

    def finish_recovery(self, server: Server, remaining: int | None) -> None:
        """Programa la reanudación después de recuperar conexiones."""
        ...


class ServerEngine:
    """Adaptador de la API pública del motor de reglas existente."""

    def __init__(self, factory: Callable[..., Server] = Server) -> None:
        """Permite reemplazar la construcción del motor sin cambiar el anfitrión."""
        self._factory = factory

    def create(self, theme: str, rules_profile: str | None = None) -> Server:
        """Crea un motor nuevo.

        Returns:
            Motor independiente, sin listener TCP.

        """
        return self._factory(theme, rules_profile=rules_profile)

    def restore(self, checkpoint: dict[str, Any]) -> Server:
        """Valida y restaura sobre un motor descartable.

        Returns:
            Motor restaurado con jugadores pendientes de reconexión.

        Raises:
            ValueError: Si el memento no es válido.

        """
        server = self.create(checkpoint.get("theme", ""))
        try:
            server.restore_state(checkpoint)
        except Exception as error:
            server.detener()
            msg = "La copia de la partida es incompatible o está incompleta"
            raise ValueError(msg) from error
        return server

    def capture(self, server: Server) -> dict[str, Any]:
        """Obtiene una transición completa.

        Returns:
            Memento del motor.

        """
        return server.capture_state()

    def finish_recovery(self, server: Server, remaining: int | None) -> None:
        """Delega al originador la reconstrucción de su reloj."""
        server.finish_recovery(remaining)
