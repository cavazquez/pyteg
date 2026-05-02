"""Carga de íconos para la barra de herramientas."""

from __future__ import annotations

from PySide6.QtGui import QIcon

from pyteg.exception import ImagenNoEncontradaError
from pyteg.utils import get_resource_path


def cargar_icono_toolbar(ruta_relativa: str, contexto: str = "") -> QIcon:
    """Valida que exista el recurso y devuelve un QIcon.

    Args:
        ruta_relativa: Ruta relativa al recurso (p. ej. ``icons/conectar.png``).
        contexto: Texto opcional para mensajes de error.

    Returns:
        Icono cargado.

    Raises:
        ImagenNoEncontradaError: Si el archivo no existe.

    """
    ruta_completa = get_resource_path(ruta_relativa)
    if not ruta_completa.exists():
        contexto_msg = f" ({contexto})" if contexto else ""
        raise ImagenNoEncontradaError(
            str(ruta_completa), f"icono de la barra de herramientas{contexto_msg}"
        )
    return QIcon(str(ruta_completa))
