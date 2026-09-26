"""Tareas del cliente: chat y errores del lobby."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QMessageBox, QWidget

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.types import ChatClientTaskData, ErrorTaskData
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskChat(IClientTask[ChatClientTaskData]):
    """Tarea para mostrar mensajes de chat."""

    def __init__(self, data: ChatClientTaskData) -> None:
        """Inicializa la tarea de chat.

        Args:
            data: Diccionario con el mensaje y tipo de mensaje.

        """
        super().__init__(data)
        self._msg = data.get("msg")
        self._msg_type = data.get("msg_type", "normal")

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea agregando el mensaje al chat."""
        if main_window.chat is None or self._msg is None:
            return
        main_window.chat.append(self._msg, self._msg_type)


class ClientTaskError(IClientTask[ErrorTaskData]):
    """Tarea para manejar errores enviados por el servidor."""

    def __init__(self, data: ErrorTaskData) -> None:
        """Inicializa la tarea de error.

        Args:
            data: Diccionario con el tipo y mensaje de error.

        """
        super().__init__(data)
        self._error_type = data.get("error_type")
        self._message = data.get("message")

    def run(self, main_window: GameWindowProtocol) -> None:
        """Maneja errores enviados por el servidor.

        Maneja errores enviados por el servidor mostrando un diálogo
        de error al usuario.
        """
        main_window.sound_manager.play_error()

        if self._error_type == "incompatible_theme":
            server_theme = getattr(
                getattr(main_window, "client_state_model", None), "theme", None
            )
            theme_names = {"classic": _("Clásico"), "revancha": _("Revancha")}
            server_name = (
                theme_names.get(server_theme) if isinstance(server_theme, str) else None
            )
            if server_name is None:
                message = _(
                    "El servidor usa otro mapa. Seleccioná el mapa de esa partida "
                    "y volvé a conectar."
                )
            else:
                message = _(
                    "El servidor usa el mapa {}. Seleccionalo y volvé a conectar."
                ).format(server_name)
            QMessageBox.warning(
                cast("QWidget", main_window), _("Mapa incompatible"), message
            )
            if main_window.conexion is not None:
                main_window.conexion.abortar()
            main_window.abrir_ventana_conectar()
        elif self._error_type == "reconnect_rejected":
            QMessageBox.warning(
                cast("QWidget", main_window),
                _("No se pudo reconectar"),
                _(
                    "La sesión anterior ya no está disponible. "
                    "Volvé a conectar con un usuario nuevo."
                ),
            )
            if main_window.conexion is not None:
                main_window.conexion.abortar()
            main_window.client.reset_session()
            main_window.client_by_id.clear()
            main_window.update_mi_jugador_info()
            main_window.abrir_ventana_conectar()
        elif self._error_type == "duplicate_username":
            msg_box = QMessageBox(cast("QWidget", main_window))
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(_("Nombre de usuario duplicado"))
            msg_box.setText(_("El nombre de usuario que elegiste ya está en uso."))
            msg_box.setInformativeText(
                _("Por favor, elige un nombre de usuario diferente.")
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            if main_window.w is not None:
                main_window.w.close()

            if main_window.conexion is not None:
                main_window.conexion.desconectar()

            main_window.abrir_ventana_conectar()
        else:
            msg_box = QMessageBox(cast("QWidget", main_window))
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(_("Error"))
            msg_box.setText(self._message or _("Ha ocurrido un error."))
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
