"""Tarea del cliente: actualizar el estado del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskEstado(IClientTask):
    """Tarea para actualizar el estado del juego."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de estado.

        Args:
            data: Diccionario con el nuevo estado del juego.

        """
        super().__init__(data)
        self._msg: str = str(data.get("estado", ""))

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea actualizando el estado del juego."""
        CLIENT_TASKS_LOG.debug("Recibido cambio de estado: %s", self._msg)

        main_window.update_game_state(self._msg)

        if self._msg == "EsperarJugadores":
            CLIENT_TASKS_LOG.debug("Mostrando ventana de espera de jugadores")
            main_window.ventana_esperar_jugadores()
        elif self._msg == "JUGANDO":
            CLIENT_TASKS_LOG.debug("Cambiando a estado JUGANDO")
            if main_window.w is not None:
                CLIENT_TASKS_LOG.debug("Cerrando ventana de espera...")
                try:
                    main_window.w.close()
                    main_window.w.deleteLater()
                    main_window.w = None
                    CLIENT_TASKS_LOG.debug("Ventana de espera cerrada correctamente")
                except (AttributeError, RuntimeError) as e:
                    CLIENT_TASKS_LOG.warning(
                        "Error al cerrar la ventana de espera: %s", e
                    )
            else:
                CLIENT_TASKS_LOG.debug("No hay ventana de espera abierta para cerrar")

            try:
                self.actualizar_lista_jugadores(main_window)
            except (AttributeError, KeyError, TypeError) as e:
                CLIENT_TASKS_LOG.warning(
                    "Error al actualizar lista de jugadores: %s", e
                )

            main_window.update()

    def actualizar_lista_jugadores(self, main_window: GameWindowProtocol) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        jugadores: list[tuple[str, Any]] = []
        for user_id, color in main_window.colores.colores_asignados().items():
            client = main_window.client_by_id.get(user_id)
            if client:
                jugadores.append((client.username(), color))

        main_window.update_player_list(jugadores)
