"""Configuración de límites del sistema de logging vía variables de entorno."""

from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    """Lee un entero desde una variable de entorno con fallback al default.

    Args:
        name: Nombre de la variable de entorno.
        default: Valor por defecto si la variable no está o es inválida.

    Returns:
        Valor entero parseado o `default`.

    """
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def get_limits() -> dict[str, int]:
    """Obtiene límites de logging desde variables de entorno con defaults.

    Returns:
        dict con keys: max_bytes, backup_count, max_total_mb, max_days,
        max_client_files.

    """
    return {
        "max_bytes": env_int("PYTEG_LOG_MAX_BYTES", 10 * 1024 * 1024),
        "backup_count": env_int("PYTEG_LOG_BACKUP_COUNT", 5),
        "max_total_mb": env_int("PYTEG_LOG_MAX_TOTAL_MB", 200),
        "max_days": env_int("PYTEG_LOG_MAX_DAYS", 14),
        "max_client_files": env_int("PYTEG_LOG_MAX_CLIENT_FILES", 20),
    }
