"""Tareas del cliente: turno, tiempo, victoria y configuración de partida."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.config import (
    DEFAULT_TURN_SECONDS,
    DEFAULT_VICTORY_COUNTRIES,
    TIMER_COLOR_GREEN_THRESHOLD,
    TIMER_COLOR_ORANGE_THRESHOLD,
)
from pyteg.i18n import _


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


class ClientTaskVictoria(IClientTask):
    """Tarea para mostrar el mensaje de victoria."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de victoria.

        Args:
            data: Diccionario con el ID y nombre del ganador.

        """
        super().__init__(data)
        self._ganador_id = data.get("ganador_id")
        self._ganador_nombre = data.get("ganador_nombre")

    def run(self, main_window: Any) -> None:
        """Muestra un mensaje de victoria cuando alguien gana la partida."""
        try:
            if hasattr(main_window, "sound_manager"):
                main_window.sound_manager.play_victory()

            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(
                    _("🏆 ¡{} ha ganado la partida!").format(self._ganador_nombre),
                    "green",
                )

            msg_box = QMessageBox(main_window)
            msg_box.setWindowTitle(_("¡Partida Terminada!"))
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(_("🏆 ¡Felicitaciones!"))
            msg_box.setInformativeText(
                _(
                    "{} ha ganado la partida controlando el número objetivo de países."
                ).format(self._ganador_nombre)
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            if hasattr(main_window, "chat"):
                main_window.chat.append(
                    _("🏆 ¡{} ha ganado la partida!").format(self._ganador_nombre),
                    "system",
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al mostrar mensaje de victoria: %s", e)


class ClientTaskConfiguracionPartida(IClientTask):
    """Tarea para procesar la configuración de la partida."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de configuración de partida.

        Args:
            data: Diccionario con la configuración de la partida.

        """
        super().__init__(data)
        self._segundos_por_turno = data.get("segundos_por_turno", DEFAULT_TURN_SECONDS)
        self._paises_para_victoria = data.get(
            "paises_para_victoria", DEFAULT_VICTORY_COUNTRIES
        )
        self._objetivos_secretos = data.get("objetivos_secretos", False)
        self._misiles_habilitados = data.get("misiles_habilitados", False)

    def run(self, main_window: Any) -> None:
        """Procesa la configuración de la partida.

        Almacena la configuración en la ventana principal.
        """
        try:
            if hasattr(main_window, "set_configuracion_partida"):
                main_window.set_configuracion_partida(
                    self._segundos_por_turno,
                    self._paises_para_victoria,
                    objetivos_secretos=self._objetivos_secretos,
                    misiles_habilitados=self._misiles_habilitados,
                )

            if hasattr(main_window, "update_status_bar"):
                if self._paises_para_victoria == 0:
                    objetivo_texto = _("todos los países")
                else:
                    objetivo_texto = _("{} países").format(self._paises_para_victoria)
                main_window.update_status_bar(
                    _("Objetivo: {} | Turno: {}s").format(
                        objetivo_texto, self._segundos_por_turno
                    ),
                    "blue",
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning(
                "Error al procesar configuración de partida: %s", e
            )


class ClientTaskObjetivoSecreto(IClientTask):
    """Tarea para procesar el objetivo secreto asignado."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de objetivo secreto.

        Args:
            data: Diccionario con el ID y descripción del objetivo secreto.

        """
        super().__init__(data)
        self._objetivo_id = data.get("objetivo_id", "")
        self._descripcion = data.get("descripcion", "")

    def run(self, main_window: Any) -> None:
        """Procesa el objetivo secreto asignado.

        Lo almacena en la ventana principal.
        """
        try:
            CLIENT_TASKS_LOG.debug(
                "ClientTaskObjetivoSecreto: objetivo_id=%s desc=%s",
                self._objetivo_id,
                self._descripcion,
            )

            if hasattr(main_window, "set_objetivo_secreto"):
                main_window.set_objetivo_secreto(self._objetivo_id, self._descripcion)
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskObjetivoSecreto: objetivo almacenado en main_window"
                )
            else:
                CLIENT_TASKS_LOG.warning(
                    "ClientTaskObjetivoSecreto: main_window carece de "
                    "set_objetivo_secreto"
                )

            if hasattr(main_window, "chat"):
                main_window.chat.append(
                    _("Objetivo secreto asignado: {}").format(self._descripcion),
                    "system",
                )
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskObjetivoSecreto: mensaje agregado al chat"
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar objetivo secreto: %s", e)
