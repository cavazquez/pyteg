"""Configuración de logging para el cliente PyTeg."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.log_cli import resolve_log_levels
from pyteg.logger import configure_logging, get_logger

if TYPE_CHECKING:
    import argparse
    import logging


def configure_client_logging(args: argparse.Namespace) -> logging.Logger:
    """Aplica niveles de logging y devuelve el logger raíz del cliente.

    Args:
        args: Argumentos parseados del cliente.

    Returns:
        Logger configurado para el arranque del cliente.

    """
    console_level, file_level = resolve_log_levels(args)
    configure_logging(console_level=console_level, file_level=file_level)
    return get_logger("pyteg.client")
