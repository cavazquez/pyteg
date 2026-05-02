"""Shim de compatibilidad: `cargar_icono_toolbar` vive en `pyteg.gui.toolbar`."""

from __future__ import annotations

from pyteg.gui.toolbar.icons import cargar_icono_toolbar

__all__ = ["cargar_icono_toolbar"]
