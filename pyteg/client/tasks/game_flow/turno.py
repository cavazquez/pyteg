"""Tareas del cliente: turno actual y tiempo restante."""

from __future__ import annotations

from typing import Any

from pyteg.client.tasks.base import IClientTask
from pyteg.config import (
    TIMER_COLOR_GREEN_THRESHOLD,
    TIMER_COLOR_ORANGE_THRESHOLD,
)


class ClientTaskTurno(IClientTask):
    """Tarea para actualizar el turno actual del juego."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de turno.

        Args:
            data: Diccionario con información del turno.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el turno en la interfaz."""
        num_turno = int(self._msg.get("num_turno", 0))
        num_ronda = int(self._msg.get("num_ronda", 1))

        jugador_actual_id = self._msg.get("jugador_actual_id")
        jugador_actual_nombre = self._msg.get("jugador_actual_nombre")
        jugador_actual_color = self._msg.get("jugador_actual_color")

        main_window.update_turno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )

        if hasattr(main_window, "sound_manager"):
            main_window.sound_manager.play_turn()

        main_window.chat.append(f"Turno {num_turno + 1} iniciado", "system")


class ClientTaskTiempo(IClientTask):
    """Tarea para actualizar el tiempo restante del turno."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de tiempo.

        Args:
            data: Diccionario con el tiempo restante.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el display del tiempo."""
        tiempo = int(self._msg.get("tiempo", 0))
        if tiempo > 0:
            if tiempo > TIMER_COLOR_GREEN_THRESHOLD:
                color = "green"
            elif tiempo > TIMER_COLOR_ORANGE_THRESHOLD:
                color = "orange"
            else:
                color = "red"

            main_window.update_timer_display(f"Tiempo: {tiempo}s", color=color)
        else:
            main_window.update_timer_display("")
