"""Módulo para gestión de la barra de estado en la interfaz gráfica.

Este módulo contiene la clase StatusManager que maneja toda la lógica
relacionada con la actualización y gestión de la barra de estado
en la interfaz gráfica principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QTimer

from pyteg.debug_logger import debug_logger
from pyteg.gui.status_bar.builder import update_status_bar_layout
from pyteg.i18n import _
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol
    from pyteg.gui.status_bar.protocols import StatusBarHost

_LOG = get_logger("gui.status_manager")

# Los resultados explícitos se reemplazan entre sí en orden de llegada; un
# mensaje genérico sin color no tapa un resultado y el hover queda por debajo.
_NOTICE_PRIORITY = {"red": 2, "orange": 2, "green": 2, "blue": 2}
_NOTICE_DURATION_MS = {"red": 6000, "orange": 4500, "green": 4000, "blue": 3000}
_NOTICE_COLORS = {
    "light": {
        "red": "#ad2626",
        "orange": "#955600",
        "green": "#216b3d",
        "blue": "#245d9e",
    },
    "dark": {
        "red": "#ff8f8f",
        "orange": "#ffc67d",
        "green": "#91dfaa",
        "blue": "#a1c6ff",
    },
}


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
        self._hover_text = ""
        self._status_tip_text = ""
        self._notice_text = ""
        self._notice_color: str | None = None
        self._notice_priority = 0
        self._notice_timer = QTimer()
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._expire_notice)
        self._round_number: int | None = None
        self._turn_number: int | None = None
        self._timer_seconds: int | None = None
        self._timer_total_seconds: int | None = None
        self._timer_color: str | None = None

    def update_status_bar(self, text: str, color: str | None = None) -> None:
        """Muestra un aviso temporizado sin perder el detalle bajo el cursor.

        Args:
            text: Mensaje para la barra de estado.
            color: Rol visual opcional: red, orange, green o blue.

        """
        if not text:
            self._expire_notice()
            return
        priority = _NOTICE_PRIORITY.get(color or "", 1)
        if self._notice_timer.isActive() and priority < self._notice_priority:
            return
        self._notice_text = text
        self._notice_color = color
        self._notice_priority = priority
        self._notice_timer.start(_NOTICE_DURATION_MS.get(color or "", 3000))
        self._render_status_message()

    def update_hover(self, text: str) -> None:
        """Conserva el detalle del mapa sin sobrescribir avisos activos."""
        self._hover_text = text
        if not self._notice_timer.isActive():
            self._render_status_message()

    def clear_hover(self) -> None:
        """Limpia sólo el detalle del cursor cuando sale del mapa."""
        self._hover_text = ""
        if not self._notice_timer.isActive():
            self._render_status_message()

    def update_status_tip(self, text: str) -> None:
        """Muestra ayuda de toolbar o menú por debajo de los avisos activos."""
        self._status_tip_text = text
        if not self._notice_timer.isActive():
            self._render_status_message()

    def _expire_notice(self) -> None:
        self._notice_timer.stop()
        self._notice_text = ""
        self._notice_color = None
        self._notice_priority = 0
        self._render_status_message()

    def _render_status_message(self) -> None:
        label = getattr(self.main_window, "status_message_label", None)
        text = self._notice_text or self._status_tip_text or self._hover_text
        if label is None:
            # Compatibilidad con hosts mínimos que sólo tienen QStatusBar.
            self.main_window.status_bar.showMessage(text)
            return
        if self._notice_text and self._notice_color:
            palette = _NOTICE_COLORS.get(
                self.main_window.theme, _NOTICE_COLORS["light"]
            )
            foreground = palette.get(self._notice_color)
            label.setStyleSheet(
                f"color: {foreground}; font-weight: 700;" if foreground else ""
            )
        else:
            label.setStyleSheet("")
        label.setText(text)
        label.setToolTip(text)

    def clear_status_bar(self) -> None:
        """Limpia avisos y detalle del cursor sin alterar la información fija."""
        self._notice_timer.stop()
        self._notice_text = ""
        self._notice_color = None
        self._notice_priority = 0
        self._hover_text = ""
        self._status_tip_text = ""
        self.main_window.status_bar.clearMessage()
        self._render_status_message()

    def update_game_state(self, estado: str) -> None:
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state

        """
        self.main_window.estado_actual = estado
        if estado == "JUGANDO":
            self.main_window.partida_finalizada = False
        elif estado in {"FINALIZADO", "Finalizado"}:
            self.main_window.partida_finalizada = True
        if estado in {"Desconectado", "INICIAL", "EsperarJugadores"}:
            # No arrastrar la fase de una partida anterior a la sala o a la
            # pantalla de conexión.
            self.main_window.fase_actual = None
            self.main_window.unidades_pendientes_servidor = 0
            self._round_number = None
            self._turn_number = None
            self.main_window.turno_label.setText(_("Turno: 0"))

        self._set_state_label(estado)
        self.update_gameplay_context()

    def _set_state_label(self, estado: str) -> None:
        """Traduce el estado técnico sin repetir efectos de cambio de fase."""
        estados_amigables = {
            "INICIAL": _("Inicial"),
            "EsperarJugadores": _("Esperando Jugadores"),
            "JUGANDO": _("En Juego"),
            "FINALIZADO": _("Finalizado"),
            "Finalizado": _("Finalizado"),
            "Conectado": _("Conectado"),
            "Desconectado": _("Desconectado"),
        }

        estado_mostrar = estados_amigables.get(estado, estado)
        self.main_window.estado_label.setText(_("Estado: {}").format(estado_mostrar))
        self.main_window.estado_label.setToolTip(self.main_window.estado_label.text())

    def _refresh_responsive_layout(self) -> None:
        if not hasattr(self.main_window, "status_bar_sections"):
            return
        update_status_bar_layout(
            cast("StatusBarHost", self.main_window), self.main_window.width()
        )

    def update_gameplay_context(self) -> None:
        """Muestra fase, jugador activo y refuerzos durante una partida."""
        from pyteg.gui.gameplay_state import contexto_partida  # noqa: PLC0415

        label = getattr(self.main_window, "contexto_partida_label", None)
        if label is None:
            return
        contexto = contexto_partida(self.main_window)
        if contexto is not None:
            label.setText(contexto)
            label.setToolTip(contexto)
            label.setVisible(True)
        else:
            label.clear()
            label.setVisible(False)
            label.setToolTip("")
        self._refresh_responsive_layout()

    def refresh_language(self) -> None:
        """Reconstruye etiquetas dinámicas desde el estado, no desde su texto."""
        self.main_window.mi_jugador_text.setText(_("Mi jugador:"))
        self.update_mi_jugador_info()
        self._set_state_label(self.main_window.estado_actual)
        if self._round_number is not None and self._turn_number is not None:
            self.main_window.turno_label.setText(
                _("Ronda: {} - Turno: {}").format(
                    self._round_number, self._turn_number + 1
                )
            )
        elif self.main_window.turno_label.text() in {
            "Esperando turno",
            "Waiting for turn",
        }:
            self.main_window.turno_label.setText(_("Esperando turno"))
        elif self.main_window.turno_label.text() in {"Turno: 0", "Turn: 0"}:
            self.main_window.turno_label.setText(_("Turno: 0"))
        self.update_gameplay_context()
        if self._timer_seconds is not None and self._timer_total_seconds is not None:
            self.update_timer_seconds(self._timer_seconds, self._timer_total_seconds)
        self._refresh_responsive_layout()

    def refresh_theme(self) -> None:
        """Reaplica colores legibles a aviso y temporizador tras cambiar tema."""
        self._render_status_message()
        self._apply_timer_color()

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
        self._round_number = num_ronda
        self._turn_number = num_turno
        self.main_window.jugador_actual_id = jugador_actual_id
        self.main_window.jugador_actual_nombre = jugador_actual_nombre
        self.main_window.jugador_actual_color = jugador_actual_color

        # Actualizar el texto del turno
        self.main_window.turno_label.setText(
            _("Ronda: {} - Turno: {}").format(num_ronda, num_turno + 1)
        )
        self._refresh_responsive_layout()

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
        self._timer_color = color
        if not text:
            self._timer_seconds = None
            self._timer_total_seconds = None
        self._apply_timer_color()
        self.main_window.timer_label.setText(text)
        self.main_window.timer_label.setToolTip(text)

    def update_timer_seconds(self, seconds: int, total_seconds: int) -> None:
        """Muestra el tiempo con umbrales proporcionales a la duración elegida."""
        seconds = max(0, seconds)
        total_seconds = max(1, total_seconds)
        if seconds * 2 > total_seconds:
            color = "green"
        elif seconds * 4 > total_seconds:
            color = "orange"
        else:
            color = "red"
        self.update_timer_display(_("Tiempo: {}s").format(seconds), color)
        self._timer_seconds = seconds
        self._timer_total_seconds = total_seconds

    def _apply_timer_color(self) -> None:
        palette = _NOTICE_COLORS.get(self.main_window.theme, _NOTICE_COLORS["light"])
        color = palette.get(self._timer_color or "")
        extra = f" color: {color};" if color else ""
        self.main_window.timer_label.setStyleSheet(
            f"font-weight: bold; padding: 2px 8px;{extra}"
        )
