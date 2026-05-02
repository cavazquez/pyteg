"""Política de retención de archivos de log."""

from __future__ import annotations

import time
from contextlib import suppress
from typing import TYPE_CHECKING

from pyteg.logger.config import get_limits

if TYPE_CHECKING:
    from pathlib import Path


def _safe_mtime(path: Path) -> float:
    with suppress(OSError):
        return path.stat().st_mtime
    return 0.0


def _safe_size(path: Path) -> int:
    with suppress(OSError):
        return path.stat().st_size
    return 0


def cleanup_logs(log_dir: Path) -> None:
    """Aplica política de retención en el directorio de logs.

    - Elimina archivos más antiguos que ``max_days``.
    - Limita la cantidad de archivos de cliente (``client_*.log``) a
      ``max_client_files``.
    - Limita el total acumulado a ``max_total_mb`` eliminando los más antiguos.

    Args:
        log_dir: Directorio de logs sobre el que aplicar la política.

    """
    limits = get_limits()
    now = time.time()
    max_age = limits["max_days"] * 24 * 3600
    max_total_bytes = limits["max_total_mb"] * 1024 * 1024

    files = [p for p in log_dir.glob("*.log") if p.is_file()]

    for p in list(files):
        mtime = _safe_mtime(p)
        if now - mtime > max_age:
            with suppress(OSError):
                p.unlink(missing_ok=True)
            with suppress(ValueError):
                files.remove(p)

    client_logs = [p for p in files if p.name.startswith("client_")]
    if len(client_logs) > limits["max_client_files"]:
        client_logs.sort(key=_safe_mtime)
        to_delete = client_logs[: len(client_logs) - limits["max_client_files"]]
        for p in to_delete:
            with suppress(OSError):
                p.unlink(missing_ok=True)
            with suppress(ValueError):
                files.remove(p)

    files.sort(key=_safe_mtime)
    total = sum(_safe_size(p) for p in files)
    while total > max_total_bytes and files:
        victim = files.pop(0)
        with suppress(OSError):
            victim.unlink(missing_ok=True)
        total = sum(_safe_size(p) for p in files)
