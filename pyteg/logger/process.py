"""Detección del tipo de proceso (server/client/unknown)."""

from __future__ import annotations

import sys
from pathlib import Path


def determine_process_type() -> str:
    """Determina el tipo de proceso basado en los argumentos del script.

    Returns:
        ``"server"``, ``"client"`` o ``"unknown"``.

    """
    if len(sys.argv) > 0:
        script_name = Path(sys.argv[0]).name.lower()
        if "server" in script_name:
            return "server"
        if "client" in script_name or "gui" in script_name:
            return "client"
    return "unknown"
