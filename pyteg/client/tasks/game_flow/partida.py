"""Tareas del cliente: configuración de partida, objetivo secreto y victoria."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from PySide6.QtWidgets import QMessageBox, QWidget

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.config import (
    DEFAULT_TURN_SECONDS,
    DEFAULT_VICTORY_COUNTRIES,
)
from pyteg.i18n import _

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


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

    def run(self, main_window: GameWindowProtocol) -> None:
        """Muestra un mensaje de victoria cuando alguien gana la partida."""
        try:
            main_window.sound_manager.play_victory()

            main_window.update_status_bar(
                _("🏆 ¡{} ha ganado la partida!").format(self._ganador_nombre),
                "green",
            )

            msg_box = QMessageBox(cast("QWidget", main_window))
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

            if main_window.chat is not None:
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

    def run(self, main_window: GameWindowProtocol) -> None:
        """Procesa la configuración de la partida.

        Almacena la configuración en la ventana principal.
        """
        try:
            main_window.set_configuracion_partida(
                self._segundos_por_turno,
                self._paises_para_victoria,
                objetivos_secretos=self._objetivos_secretos,
                misiles_habilitados=self._misiles_habilitados,
            )

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

    def run(self, main_window: GameWindowProtocol) -> None:
        """Procesa el objetivo secreto asignado.

        Lo almacena en la ventana principal.
        """
        try:
            CLIENT_TASKS_LOG.debug(
                "ClientTaskObjetivoSecreto: objetivo_id=%s desc=%s",
                self._objetivo_id,
                self._descripcion,
            )

            main_window.set_objetivo_secreto(self._objetivo_id, self._descripcion)
            CLIENT_TASKS_LOG.debug(
                "ClientTaskObjetivoSecreto: objetivo almacenado en main_window"
            )

            if main_window.chat is not None:
                main_window.chat.append(
                    _("Objetivo secreto asignado: {}").format(self._descripcion),
                    "system",
                )
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskObjetivoSecreto: mensaje agregado al chat"
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar objetivo secreto: %s", e)
