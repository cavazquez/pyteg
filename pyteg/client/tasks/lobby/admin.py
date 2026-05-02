"""Tarea del cliente: convertir al cliente en administrador."""

from __future__ import annotations

from typing import Any

from pyteg.client.tasks.base import IClientTask


class ClientTaskSerAdmin(IClientTask):
    """Tarea para convertir al cliente en administrador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de administrador.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        super().__init__(data)

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea convirtiendo al cliente en administrador."""
        main_window.client.ahora_es_admin()
        main_window.ventana_admin()
