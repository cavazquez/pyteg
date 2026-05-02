"""Handlers de archivo y consola para el logger de PyTeg."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path

from pyteg.logger.config import get_limits
from pyteg.logger.formatter import create_formatter


def setup_file_handler(
    logger: logging.Logger, filename: str, process_type: str
) -> None:
    """Configura el handler de archivo con rotación.

    Args:
        logger: Logger a configurar.
        filename: Nombre del archivo de log (relativo a ``PYTEG_LOG_DIR``).
        process_type: Tipo de proceso (``server``/``client``/``unknown``).

    """
    log_dir = Path(os.getenv("PYTEG_LOG_DIR", "logs"))
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / filename
    limits = get_limits()

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=limits["max_bytes"],
        backupCount=limits["backup_count"],
        encoding="utf-8",
        delay=True,
    )
    file_handler.setFormatter(create_formatter(process_type))
    logger.addHandler(file_handler)


def setup_console_handler(logger: logging.Logger, process_type: str) -> None:
    """Configura el handler de consola.

    Args:
        logger: Logger a configurar.
        process_type: Tipo de proceso.

    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(create_formatter(process_type))
    console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)
