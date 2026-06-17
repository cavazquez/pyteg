"""Flags y resolución de niveles de logging para apps CLI de PyTeg."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

LOG_LEVEL_CHOICES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def resolve_log_levels(args: argparse.Namespace) -> tuple[int, int]:
    """Resuelve niveles de consola y archivo según flags de CLI.

    Args:
        args: Namespace con atributos ``verbose``, ``quiet`` y ``log_level``.

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


def add_log_arguments(
    parser: argparse.ArgumentParser,
    *,
    verbose_help: str = "Nivel DEBUG en consola",
) -> None:
    """Registra flags de logging comunes en un ``ArgumentParser``.

    Args:
        parser: Parser al que añadir los argumentos.
        verbose_help: Texto de ayuda para ``-v`` / ``--verbose``.

    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=verbose_help,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Solo errores en consola (nivel ERROR)",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVEL_CHOICES,
        default=None,
        metavar="LEVEL",
        help=(
            "Nivel de log en consola "
            f"({', '.join(LOG_LEVEL_CHOICES)}; predeterminado: INFO)"
        ),
    )
