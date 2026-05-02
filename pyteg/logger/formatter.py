"""Formateador estándar para los logs de PyTeg."""

from __future__ import annotations

import logging
import os


def create_formatter(process_type: str) -> logging.Formatter:
    """Crea un formateador para los logs.

    Args:
        process_type: Tipo de proceso (``server``, ``client``, ``unknown``).

    Returns:
        Formateador configurado con timestamps y contexto de proceso.

    """
    pid = os.getpid()
    format_string = (
        f"[%(asctime)s] [{process_type.upper()}:{pid}] "
        f"[%(levelname)s] [%(name)s] %(message)s"
    )
    return logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
