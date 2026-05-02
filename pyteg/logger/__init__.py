"""Sistema de logging profesional para PyTeg.

Este paquete proporciona un sistema de logging unificado para servidor y
cliente, basado en el módulo `logging` estándar de Python.

Características:
- Niveles estándar: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- Separación servidor/cliente con archivos independientes.
- Formato consistente con timestamps y contexto.
- Rotación automática de archivos.
- Configuración flexible.
- Política de retención configurable vía variables de entorno.

Estructura interna:
- `config`: límites desde variables de entorno (`PYTEG_LOG_*`).
- `retention`: política de retención (`cleanup_logs`).
- `formatter`: formato estándar de las líneas.
- `handlers`: handlers de archivo (rotación) y consola.
- `process`: detección server/client/unknown desde `sys.argv`.
- `manager`: clase orquestadora `PyTegLogger`.
"""

from __future__ import annotations

import logging

from pyteg.logger.manager import PyTegLogger

_pyteg_logger = PyTegLogger()


def get_logger(name: str | None = None) -> logging.Logger:
    """Obtiene un logger configurado para PyTeg.

    Args:
        name: Nombre del logger (opcional).

    Returns:
        Logger configurado.

    Example:
        >>> from pyteg.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("Mensaje de información")
        >>> logger.warning("Mensaje de advertencia")
        >>> logger.error("Mensaje de error")

    """
    return _pyteg_logger.get_logger(name)


def set_console_level(level: int) -> None:
    """Cambia el nivel de logging para consola."""
    _pyteg_logger.set_console_level(level)


def set_file_level(level: int) -> None:
    """Cambia el nivel de logging para archivos."""
    _pyteg_logger.set_file_level(level)


def configure_logging(
    console_level: int = logging.WARNING, file_level: int = logging.INFO
) -> None:
    """Configura los niveles de logging globalmente.

    Args:
        console_level: Nivel para salida de consola.
        file_level: Nivel para archivos de log.

    """
    set_console_level(console_level)
    set_file_level(file_level)


logger = get_logger(__name__)


__all__ = [
    "PyTegLogger",
    "configure_logging",
    "get_logger",
    "logger",
    "set_console_level",
    "set_file_level",
]
