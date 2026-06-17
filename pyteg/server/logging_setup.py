"""Configuración de logging para el servidor PyTeg."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyteg.logger import configure_logging, get_logger

if TYPE_CHECKING:
    import argparse

LOG_LEVEL_CHOICES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def resolve_log_levels(args: argparse.Namespace) -> tuple[int, int]:
    """Resuelve niveles de consola y archivo según flags de CLI.

    Args:
        args: Argumentos parseados del servidor.

    Returns:
        Par (nivel consola, nivel archivo).

    """
    if args.log_level is not None:
        level = getattr(logging, args.log_level)
        file_level = logging.DEBUG if level == logging.DEBUG else logging.INFO
        return level, file_level
    if args.quiet:
        return logging.ERROR, logging.INFO
    if args.verbose:
        return logging.DEBUG, logging.DEBUG
    return logging.INFO, logging.INFO


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
