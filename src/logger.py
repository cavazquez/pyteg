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
- Política de retención configurable vía variables de entorno
"""

import datetime
import inspect
import logging
import logging.handlers
import os
import sys
import time
from contextlib import suppress
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
        # Aplicar política de retención al iniciar
        self._cleanup_logs(log_dir)

    @staticmethod
    def _safe_mtime(path: Path) -> float:
        with suppress(OSError):
            return path.stat().st_mtime
        return 0.0

    @staticmethod
    def _safe_size(path: Path) -> int:
        with suppress(OSError):
            return path.stat().st_size
        return 0

    def _get_limits(self) -> dict[str, int]:
        """Obtiene límites de logging desde variables de entorno con defaults.

        Returns:
            dict: max_bytes, backup_count, max_total_mb, max_days, max_client_files
        """

        def _env_int(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, default))
            except (TypeError, ValueError):
                return default

        return {
            "max_bytes": _env_int("PYTEG_LOG_MAX_BYTES", 10 * 1024 * 1024),
            "backup_count": _env_int("PYTEG_LOG_BACKUP_COUNT", 5),
            "max_total_mb": _env_int("PYTEG_LOG_MAX_TOTAL_MB", 200),
            "max_days": _env_int("PYTEG_LOG_MAX_DAYS", 14),
            "max_client_files": _env_int("PYTEG_LOG_MAX_CLIENT_FILES", 20),
        }

    def _cleanup_logs(self, log_dir: Path) -> None:
        """Aplica política de retención en el directorio de logs.

        - Elimina archivos más antiguos que max_days.
        - Limita el total acumulado a max_total_mb eliminando los más antiguos.
        - Limita la cantidad de archivos de cliente (client_*.log) a max_client_files.
        """
        limits = self._get_limits()
        now = time.time()
        max_age = limits["max_days"] * 24 * 3600
        max_total_bytes = limits["max_total_mb"] * 1024 * 1024

        files = [p for p in log_dir.glob("*.log") if p.is_file()]

        # 1) Eliminar por antigüedad
        for p in list(files):
            mtime = self._safe_mtime(p)
            if now - mtime > max_age:
                with suppress(OSError):
                    p.unlink(missing_ok=True)
                with suppress(ValueError):
                    files.remove(p)

        # 2) Limitar cantidad de client_*.log
        client_logs = [p for p in files if p.name.startswith("client_")]
        if len(client_logs) > limits["max_client_files"]:
            client_logs.sort(key=self._safe_mtime)
            to_delete = client_logs[: len(client_logs) - limits["max_client_files"]]
            for p in to_delete:
                with suppress(OSError):
                    p.unlink(missing_ok=True)
                with suppress(ValueError):
                    files.remove(p)

        # 3) Limitar tamaño total
        files.sort(key=self._safe_mtime)  # más antiguos primero
        total = sum(self._safe_size(p) for p in files)
        while total > max_total_bytes and files:
            victim = files.pop(0)
            with suppress(OSError):
                victim.unlink(missing_ok=True)
            total = sum(self._safe_size(p) for p in files)

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
        log_dir = Path(os.getenv("PYTEG_LOG_DIR", "logs"))
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / filename
        limits = self._get_limits()

        # Rotación por tamaño. El nombre ya incluye fecha y hora.
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=limits["max_bytes"],
            backupCount=limits["backup_count"],
            encoding="utf-8",
            delay=True,
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
            # Incluir fecha y hora local: pyteg_YYYY-MM-DD_HH.log
            date_hour = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H")
            default_name = f"pyteg_{date_hour}.log"
            log_filename = os.getenv("PYTEG_LOG_FILE", default_name)

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
