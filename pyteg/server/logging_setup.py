"""Configuración de logging para el servidor PyTeg."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.log_cli import LOG_LEVEL_CHOICES, resolve_log_levels
from pyteg.logger import configure_logging, get_logger

if TYPE_CHECKING:
    import argparse
    import logging

__all__ = ["LOG_LEVEL_CHOICES", "configure_server_logging", "resolve_log_levels"]


def configure_server_logging(args: argparse.Namespace) -> logging.Logger:
    """Aplica niveles de logging y devuelve el logger raíz del servidor.

    Args:
        args: Argumentos parseados del servidor.

    Returns:
        Logger configurado para el arranque del servidor.

    """
    console_level, file_level = resolve_log_levels(args)
    configure_logging(console_level=console_level, file_level=file_level)
    return get_logger("pyteg.server")
