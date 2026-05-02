"""Tareas del cliente: colores disponibles y asignados."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.client.colores.color import Color
from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskColorAsignado(IClientTask):
    """Tarea para asignar un color a un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de asignación de color.

        Args:
            data: Diccionario con el ID del usuario y los componentes RGB del color.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea asignando el color al jugador."""
        try:
            id_user = self._msg.get("id")
            if not id_user:
                CLIENT_TASKS_LOG.warning(
                    "No se proporcionó ID de usuario en el mensaje de color asignado"
                )
                return

            r = self._msg.get("r", 0)
            g = self._msg.get("g", 0)
            b = self._msg.get("b", 0)

            CLIENT_TASKS_LOG.debug(
                "Asignando color al jugador %s: R=%s, G=%s, B=%s",
                id_user,
                r,
                g,
                b,
            )

            color_data = {"r": r, "g": g, "b": b}
            main_window.colores.asignar(id_user, color_data)

            self.actualizar_lista_jugadores(main_window)

            if main_window.w is not None and hasattr(
                main_window.w, "cargar_colores_asignados"
            ):
                main_window.w.cargar_colores_asignados()

            if main_window.client:
                mi_user_id = main_window.client.userid()
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskColorAsignado: Mi user_id: %s, Color asignado a: %s",
                    mi_user_id,
                    id_user,
                )
                if mi_user_id == id_user:
                    CLIENT_TASKS_LOG.debug(
                        "ClientTaskColorAsignado: ES MI COLOR, actualizando mi info"
                    )
                    main_window.update_mi_jugador_info()
                else:
                    CLIENT_TASKS_LOG.debug(
                        "ClientTaskColorAsignado: NO es mi color, no actualizo"
                    )

        except (AttributeError, KeyError, ValueError) as e:
            CLIENT_TASKS_LOG.warning("Error en ClientTaskColorAsignado: %s", e)

    def actualizar_lista_jugadores(self, main_window: GameWindowProtocol) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        try:
            jugadores: list[tuple[str, Any]] = []
            for user_id, color in main_window.colores.colores_asignados().items():
                client = main_window.client_by_id.get(user_id)
                if client and hasattr(client, "username"):
                    jugadores.append((client.username(), color))
                    CLIENT_TASKS_LOG.debug(
                        "Jugador %s tiene color %s",
                        client.username(),
                        color.getRgb(),
                    )

            main_window.update_player_list(jugadores)
        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al actualizar lista de jugadores: %s", e)


class ClientTaskColor(IClientTask):
    """Tarea para agregar un color disponible."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de color.

        Args:
            data: Diccionario con los componentes RGB del color.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea agregando el color a la lista de colores disponibles."""
        self._msg.pop("mensaje")
        main_window.colores.agregar_color(Color(**self._msg))
