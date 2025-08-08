"""
Sistema de logging profesional para PyTeg.

Este módulo proporciona un sistema de logging unificado para servidor y cliente,
basado en el módulo logging estándar de Python.

Características:
- Niveles estándar: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Separación servidor/cliente con archivos independientes
- Formato consistente con timestamps y contexto
- Rotación automática de archivos
- Configuración flexible
"""

import inspect
import logging
import logging.handlers
import os
import sys
from pathlib import Path


class PyTegLogger:
    """
    Logger personalizado para PyTeg que maneja servidor y cliente por separado.
    """

    def __init__(self):
        self._loggers = {}
        self._setup_directories()

    def _setup_directories(self):
        """Crea los directorios necesarios para los logs."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

    def _determine_process_type(self) -> str:
        """
        Determina el tipo de proceso basado en los argumentos del script.

        Returns:
            str: 'server', 'client', o 'unknown'
        """
        if len(sys.argv) > 0:
            script_name = Path(sys.argv[0]).name.lower()
            if "server" in script_name:
                return "server"
            if "client" in script_name or "gui" in script_name:
                return "client"
        return "unknown"

    def _create_formatter(self, process_type: str) -> logging.Formatter:
        """
        Crea un formateador para los logs.

        Args:
            process_type: Tipo de proceso ('server', 'client', 'unknown')

        Returns:
            logging.Formatter: Formateador configurado
        """
        pid = os.getpid()
        format_string = (
            f"[%(asctime)s] [{process_type.upper()}:{pid}] "
            f"[%(levelname)s] [%(name)s] %(message)s"
        )

        return logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    def _setup_file_handler(
        self, logger: logging.Logger, filename: str, process_type: str
    ) -> None:
        """
        Configura el handler de archivo con rotación.

        Args:
            logger: Logger a configurar
            filename: Nombre del archivo de log
            process_type: Tipo de proceso
        """
        log_path = Path("logs") / filename

        # Usar RotatingFileHandler para rotación automática
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB por archivo
            backupCount=5,  # Mantener 5 archivos de backup
            encoding="utf-8",
        )

        file_handler.setFormatter(self._create_formatter(process_type))
        logger.addHandler(file_handler)

    def _setup_console_handler(self, logger: logging.Logger, process_type: str) -> None:
        """
        Configura el handler de consola.

        Args:
            logger: Logger a configurar
            process_type: Tipo de proceso
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._create_formatter(process_type))

        # Solo mostrar WARNING y superior en consola por defecto
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """
        Obtiene un logger configurado para el contexto actual.

        Args:
            name: Nombre del logger (opcional, usa el módulo llamador por defecto)

        Returns:
            logging.Logger: Logger configurado
        """
        if name is None:
            # Obtener el nombre del módulo llamador
            frame = inspect.currentframe()
            caller = frame.f_back if frame is not None else None
            if caller is not None:
                name = caller.f_globals.get("__name__", "unknown")
            else:
                name = "unknown"

        # Si ya existe el logger, devolverlo
        if name in self._loggers:
            return self._loggers[name]

        # Crear nuevo logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Permitir todos los niveles

        # Evitar duplicar handlers si ya están configurados
        if not logger.handlers:
            process_type = self._determine_process_type()
            pid = os.getpid()

            # Configurar archivo de log según el tipo de proceso
            if process_type == "server":
                log_filename = "server.log"
            elif process_type == "client":
                log_filename = f"client_{pid}.log"
            else:
                log_filename = f"pyteg_{pid}.log"

            # Configurar handlers
            self._setup_file_handler(logger, log_filename, process_type)
            self._setup_console_handler(logger, process_type)

        # Guardar referencia
        self._loggers[name] = logger
        return logger

    def set_console_level(self, level: int) -> None:
        """
        Cambia el nivel de logging para la consola en todos los loggers.

        Args:
            level: Nivel de logging (logging.DEBUG, INFO, WARNING, etc.)
        """
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if (
                    isinstance(handler, logging.StreamHandler)
                    and handler.stream == sys.stdout
                ):
                    handler.setLevel(level)

    def set_file_level(self, level: int) -> None:
        """
        Cambia el nivel de logging para archivos en todos los loggers.

        Args:
            level: Nivel de logging (logging.DEBUG, INFO, WARNING, etc.)
        """
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.setLevel(level)


# Instancia global del sistema de logging
_pyteg_logger = PyTegLogger()


# Función de conveniencia para obtener un logger
def get_logger(name: str | None = None) -> logging.Logger:
    """
    Obtiene un logger configurado para PyTeg.

    Args:
        name: Nombre del logger (opcional)

    Returns:
        logging.Logger: Logger configurado

    Example:
        >>> from src.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("Mensaje de información")
        >>> logger.warning("Mensaje de advertencia")
        >>> logger.error("Mensaje de error")
    """
    return _pyteg_logger.get_logger(name)


# Logger por defecto para uso directo
logger = get_logger(__name__)


# Funciones de conveniencia para configuración
def set_console_level(level: int) -> None:
    """Cambia el nivel de logging para consola."""
    _pyteg_logger.set_console_level(level)


def set_file_level(level: int) -> None:
    """Cambia el nivel de logging para archivos."""
    _pyteg_logger.set_file_level(level)


# Configuración inicial
def configure_logging(
    console_level: int = logging.WARNING, file_level: int = logging.INFO
) -> None:
    """
    Configura los niveles de logging globalmente.

    Args:
        console_level: Nivel para salida de consola
        file_level: Nivel para archivos de log
    """
    set_console_level(console_level)
    set_file_level(file_level)
