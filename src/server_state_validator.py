"""Validador de acciones del servidor basadas en estado."""

from __future__ import annotations

from typing import Protocol

from src.exception import EstadoInvalidoError
from src.server_estado import Estado


class HasEstado(Protocol):
    estado: Estado


class ServerStateValidator:
    """Encargado de validar si una acción puede ejecutarse según el estado."""

    def validar_accion(self, action_name: str, server: HasEstado) -> None:
        """Valida si una acción puede ejecutarse.

        Raises:
            EstadoInvalidoError: Si la acción no está permitida en el estado actual.
        """
        if not action_name:
            return

        if not server.estado.puede_ejecutar_accion(action_name):
            acciones_validas = Estado.get_acciones_validas()
            estados_validos = acciones_validas.get(action_name, [])
            raise EstadoInvalidoError(
                action_name, server.estado.estado_actual(), estados_validos
            )

    def puede_ejecutar(self, action_name: str, server: HasEstado) -> bool:
        """Verifica si una acción puede ejecutarse sin lanzar excepción."""
        try:
            self.validar_accion(action_name, server)
        except EstadoInvalidoError:
            return False
        else:
            return True
