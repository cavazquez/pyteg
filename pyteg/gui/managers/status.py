"""Módulo para gestión de la barra de estado en la interfaz gráfica.

Este módulo contiene la clase StatusManager que maneja toda la lógica
relacionada con la actualización y gestión de la barra de estado
en la interfaz gráfica principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel

from pyteg.debug_logger import debug_logger
from pyteg.i18n import _
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol

_LOG = get_logger("gui.status_manager")


class StatusManager:
    """Gestiona la barra de estado y la información del jugador actual.

    Esta clase se encarga de actualizar mensajes en la barra de estado,
    gestionar el estado del juego y mantener la información del jugador actual.
    """

    def __init__(self, main_window: MainWindowProtocol):
        """Inicializa el gestor de estado.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def update_status_bar(self, text: str, color: str | None = None) -> None:
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
            color (str, optional): Color for the text (e.g., 'green', 'red', '#ff0000')

        """
        # Apply color styling if provided
        if color:
            # Create a temporary label to apply color styling
            temp_label = getattr(self.main_window, "status_temp_label", None)
            if temp_label is None:
                temp_label = QLabel()
                self.main_window.status_temp_label = temp_label
                status_bar = self.main_window.status_bar
                status_bar.addWidget(temp_label)

            temp_label.setText(text)
            temp_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            # Clear the default message to avoid duplication
            self.main_window.status_bar.clearMessage()
        else:
            # Use default status bar message
            temp_label = getattr(self.main_window, "status_temp_label", None)
            if temp_label is not None:
                temp_label.setText("")
            self.main_window.status_bar.showMessage(text)

    def clear_status_bar(self) -> None:
        """Clear the status bar message, but keep the turn number."""
        self.main_window.status_bar.clearMessage()
        # Also clear the temporary colored label if it exists
        temp_label = getattr(self.main_window, "status_temp_label", None)
        if temp_label is not None:
            temp_label.setText("")

    def update_game_state(self, estado: str) -> None:
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state

        """
        # Traducir estados técnicos a nombres más amigables
        estados_amigables = {
            "INICIAL": _("Inicial"),
            "EsperarJugadores": _("Esperando Jugadores"),
            "JUGANDO": _("En Juego"),
            "FINALIZADO": _("Finalizado"),
            "Conectado": _("Conectado"),
            "Desconectado": _("Desconectado"),
        }

        estado_mostrar = estados_amigables.get(estado, estado)
        self.main_window.estado_label.setText(_("Estado: {}").format(estado_mostrar))

    def update_mi_jugador_info(self) -> None:
        """Actualiza la información del usuario actual (mi jugador).

        Actualiza la información en la barra de estado.
        """
        try:
            debug_logger.log("GUI: update_mi_jugador_info llamado")
            # Verificar que tenemos un cliente conectado
            client = getattr(self.main_window, "client", None)
            if client is None or not client.userid():
                debug_logger.log("GUI: No hay cliente conectado")
                self.main_window.mi_username_label.setText(_("[No conectado]"))
                self.main_window.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
                return

            # Obtener mi usuario ID
            mi_user_id = client.userid()
            debug_logger.log(f"GUI: Mi user_id: {mi_user_id}")

            # Obtener mi nombre de usuario
            mi_username = client.username() or _("[Sin nombre]")
            debug_logger.log(f"GUI: Mi username: {mi_username}")

            # Obtener mi color asignado
            mi_color = None
            colores = getattr(self.main_window, "colores", None)
            if colores is not None:
                mi_color = colores.color_asignado(mi_user_id)
                debug_logger.log(f"GUI: Mi color: {mi_color}")

            # Actualizar el nombre de usuario
            self.main_window.mi_username_label.setText(mi_username)

            # Actualizar el color
            if mi_color and hasattr(mi_color, "name"):
                color_hex = mi_color.name()  # Obtener color en formato hexadecimal
                debug_logger.log(f"GUI: Color hex: {color_hex}")
                self.main_window.mi_color_indicator.setStyleSheet(f"""
                    background-color: {color_hex};
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
            else:
                debug_logger.log("GUI: No hay color asignado, usando color por defecto")
                # Color por defecto si no hay color asignado
                self.main_window.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
        except (AttributeError, KeyError, ValueError) as e:
            _LOG.warning("Error al actualizar información de mi jugador: %s", e)
            self.main_window.mi_username_label.setText(_("[Error]"))

    def update_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Actualiza el número de turno y ronda, y la información del jugador actual.

        Args:
            num_turno: Número del turno actual.
            num_ronda: Número de la ronda actual.
            jugador_actual_id: ID del jugador actual.
            jugador_actual_nombre: Nombre del jugador actual.
            jugador_actual_color: Color del jugador actual.

        """
        # Almacenar información del turno (usando atributos públicos)
        self.main_window.turno_actual = num_turno
        self.main_window.jugador_actual_id = jugador_actual_id
        self.main_window.jugador_actual_nombre = jugador_actual_nombre
        self.main_window.jugador_actual_color = jugador_actual_color

        # Actualizar el texto del turno
        self.main_window.turno_label.setText(
            _("Ronda: {} - Turno: {}").format(num_ronda, num_turno + 1)
        )

        # Actualizar sombreado del jugador en su turno
        if jugador_actual_nombre:
            self.main_window.players_manager.set_current_player(jugador_actual_nombre)

        from pyteg.gui.gameplay_state import refresh_acciones_juego  # noqa: PLC0415

        refresh_acciones_juego(self.main_window)

    def update_timer_display(self, text: str, color: str | None = None) -> None:
        """Actualiza el display del timer en la barra de estado.

        Args:
            text: Texto del timer a mostrar.
            color: Color para el texto (opcional).

        """
        if color:
            self.main_window.timer_label.setStyleSheet(
                f"font-weight: bold; padding: 2px 8px; color: {color};"
            )
        else:
            self.main_window.timer_label.setStyleSheet(
                "font-weight: bold; padding: 2px 8px;"
            )
        self.main_window.timer_label.setText(text)
