"""Tareas del cliente: chat y errores del lobby."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from PySide6.QtWidgets import QMessageBox, QWidget

from pyteg.client.tasks.base import IClientTask
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskChat(IClientTask):
    """Tarea para mostrar mensajes de chat."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de chat.

        Args:
            data: Diccionario con el mensaje y tipo de mensaje.

        """
        super().__init__(data)
        self._msg = data.get("msg")
        self._msg_type = data.get("msg_type", "normal")

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea agregando el mensaje al chat."""
        main_window.chat.append(self._msg, self._msg_type)


class ClientTaskError(IClientTask):
    """Tarea para manejar errores enviados por el servidor."""

    def __init__(self, data: dict[str, Any]) -> None:
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
        if self._error_type == "duplicate_username":
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
