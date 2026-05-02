"""Excepción base de PyTeg."""

from __future__ import annotations


class PyTegError(Exception):
    """Excepción base para todos los errores de PyTeg."""

    def __init__(self, msg: str) -> None:
        """Inicializa la excepción con un mensaje.

        Args:
            msg: Mensaje de error.

        """
        super().__init__(msg)
        self.mensaje = msg
