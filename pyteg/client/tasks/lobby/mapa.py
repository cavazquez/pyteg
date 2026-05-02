"""Tareas del cliente: asignación inicial de países y unidades disponibles."""

from __future__ import annotations

from typing import Any

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG


class ClientTaskAsignarPais(IClientTask):
    """Tarea para asignar un país a un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de asignación de país.

        Args:
            data: Diccionario con el país, ID de usuario y unidades.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea asignando el país al jugador."""
        try:
            nombre_pais = self._msg.get("pais")
            userid = self._msg.get("userid")
            unidades = self._msg.get("unidades", 1)

            pais = main_window.scene.paises.get(nombre_pais)
            if not pais:
                CLIENT_TASKS_LOG.warning("País no encontrado: %s", nombre_pais)
                return

            pais.set_unidades(unidades)

            color = main_window.colores.color_asignado(userid)
            if not color:
                CLIENT_TASKS_LOG.warning(
                    "No se encontró color para el jugador %s", userid
                )
                return

            pais.set_color(color)

            CLIENT_TASKS_LOG.debug(
                "País %s asignado al jugador %s con %s unidades y color %s",
                nombre_pais,
                userid,
                unidades,
                color.getRgb(),
            )

        except (AttributeError, KeyError, ValueError) as e:
            CLIENT_TASKS_LOG.warning("Error al asignar país: %s", e)


class ClientTaskUnidadesDisponibles(IClientTask):
    """Tarea para actualizar las unidades disponibles del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de unidades disponibles.

        Args:
            data: Diccionario con las unidades disponibles por tipo.

        """
        super().__init__(data)
        self._unidades = data.get("unidades", {})

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando las unidades disponibles."""
        CLIENT_TASKS_LOG.debug("Recibidas unidades disponibles: %s", self._unidades)
        if hasattr(main_window, "update_unidades_disponibles"):
            main_window.update_unidades_disponibles(self._unidades)
