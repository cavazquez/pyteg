"""Orquestador del sistema de logging de PyTeg (`PyTegLogger`)."""

from __future__ import annotations

import datetime
import inspect
import logging
import logging.handlers
import os
import sys
from pathlib import Path

from pyteg.logger.handlers import setup_console_handler, setup_file_handler
from pyteg.logger.process import determine_process_type
from pyteg.logger.retention import cleanup_logs


class PyTegLogger:
    """Logger personalizado para PyTeg que maneja servidor y cliente por separado."""

    def __init__(self) -> None:
        """Inicializa el sistema de logging de PyTeg."""
        self._loggers: dict[str, logging.Logger] = {}
        self._console_level = logging.WARNING
        self._file_level = logging.INFO
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Crea los directorios necesarios y aplica retención al iniciar."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        cleanup_logs(log_dir)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Obtiene un logger configurado para el contexto actual.

        Args:
            name: Nombre del logger (opcional, usa el módulo llamador por defecto).

        Returns:
            Logger configurado.

        """
        if name is None:
            frame = inspect.currentframe()
            caller = frame.f_back if frame is not None else None
            if caller is not None:
                name = caller.f_globals.get("__name__", "unknown")
            else:
                name = "unknown"

        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            process_type = determine_process_type()
            date_hour = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H")
            default_name = f"pyteg_{date_hour}.log"
            log_filename = os.getenv("PYTEG_LOG_FILE", default_name)

            setup_file_handler(logger, log_filename, process_type)
            setup_console_handler(logger, process_type)
            for handler in logger.handlers:
                if (
                    isinstance(handler, logging.StreamHandler)
                    and handler.stream == sys.stdout
                ):
                    handler.setLevel(self._console_level)
                elif isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.setLevel(self._file_level)

        self._loggers[name] = logger
        return logger

    def set_console_level(self, level: int) -> None:
        """Cambia el nivel de logging para la consola en todos los loggers.

        Args:
            level: Nivel de logging (logging.DEBUG, INFO, WARNING, etc.).

        """
        self._console_level = level
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if (
                    isinstance(handler, logging.StreamHandler)
                    and handler.stream == sys.stdout
                ):
                    handler.setLevel(level)

    def set_file_level(self, level: int) -> None:
        """Cambia el nivel de logging para archivos en todos los loggers.

        Args:
            level: Nivel de logging (logging.DEBUG, INFO, WARNING, etc.).

        """
        self._file_level = level
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.setLevel(level)
