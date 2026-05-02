"""Módulo principal de la interfaz gráfica del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QMainWindow, QWidget

from pyteg.client.colores.paleta import Colores
from pyteg.client.conexion.transmisor import ClientNullTransmisor
from pyteg.gui.managers.cards import CardManager
from pyteg.gui.managers.config import ConfigManager
from pyteg.gui.managers.game_actions import GameActionsManager
from pyteg.gui.managers.language import LanguageManager
from pyteg.gui.managers.layout import LayoutManager
from pyteg.gui.managers.players import PlayersManager
from pyteg.gui.managers.status import StatusManager
from pyteg.gui.managers.theme import ThemeManager
from pyteg.gui.managers.units import UnitsManager
from pyteg.gui.managers.window import WindowManager
from pyteg.gui.status_bar import build_status_bar
from pyteg.i18n import translate as _
from pyteg.sound_manager import SoundManager

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtGui import QCloseEvent, QColor, QKeyEvent
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QStatusBar

    from pyteg.client.app import Client
    from pyteg.gui.dialogs.conectar import VentanaConectar
    from pyteg.gui.mapa.scene import QCustomGraphicsScene
    from pyteg.gui.toolbar import ToolBar
    from pyteg.gui.widgets.chat import Chat
    from pyteg.gui.widgets.language_selector import LanguageSelector
    from pyteg.gui.widgets.sound_control import SoundControlWidget
    from pyteg.gui.widgets.view import QCustomGraphicsView


class Gui(QMainWindow):
    """Ventana principal de la interfaz gráfica del juego."""

    status_bar: QStatusBar
    jugador_actual_widget: QWidget
    jugador_actual_layout: QHBoxLayout
    turno_label: QLabel
    mi_jugador_widget: QWidget
    mi_jugador_layout: QHBoxLayout
    mi_jugador_text: QLabel
    mi_color_indicator: QLabel
    mi_username_label: QLabel
    estado_label: QLabel
    seleccion_label: QLabel
    language_selector: LanguageSelector
    sound_control: SoundControlWidget
    timer_label: QLabel

    def __init__(self, client: Client) -> None:
        """Inicializa la ventana principal de la GUI.

        Args:
            client: Cliente del juego.

        """
        super().__init__()
        self._gui_init_core_state(client)
        self._gui_init_window_and_managers()
        self._gui_init_turn_tracking()
        self.layout_manager.setup_graphics_view()
        build_status_bar(self)
        self.show()

    def _gui_init_core_state(self, client: Client) -> None:
        self._vivo = True
        self.client = client
        self._theme = "light"
        self.client_by_id: dict[int, Any] = {}
        self.transmisor = ClientNullTransmisor()
        self.conexion: Any = None
        self.w: QWidget | None = None
        self.ventana_conectar: VentanaConectar | None = None
        self.scene: QCustomGraphicsScene | None = None
        self.view: QCustomGraphicsView | None = None
        self.chat: Chat | None = None
        self.toolbar: ToolBar | None = None

    def _gui_init_window_and_managers(self) -> None:
        self.setWindowTitle(_("PyTeg"))
        self.resize(QSize(1280, 800))
        self.layout_manager = LayoutManager(self)
        self.theme_manager = ThemeManager(self)
        self.players_manager = PlayersManager(self)
        self.status_manager = StatusManager(self)
        self.units_manager = UnitsManager(self)
        self.game_actions_manager = GameActionsManager(self)
        self.config_manager = ConfigManager(self)
        self.card_manager = CardManager(self)
        self.window_manager = WindowManager(self)
        self.language_manager = LanguageManager(self)
        self.sound_manager = SoundManager()
        self.setMinimumSize(QSize(800, 600))
        self.setMouseTracking(True)

    def _gui_init_turn_tracking(self) -> None:
        self._turno_actual = 0
        self._jugador_actual_id = None
        self._jugador_actual_nombre = None
        self._jugador_actual_color = None
        self.colores = Colores()

    def vivo(self) -> bool:
        """Verifica si la ventana está activa.

        Returns:
            True si la ventana está activa, False en caso contrario.

        """
        return self._vivo

    def update_player_list(self, players: Sequence[tuple[str, QColor]]) -> None:
        """Actualiza la lista de jugadores.

        Solo muestra los jugadores que están realmente jugando.

        Args:
            players: Lista de tuplas (nombre, color) donde color es un QColor.

        """
        self.players_manager.update_player_list(players)

    def abrir_ventana_conectar(self) -> None:
        """Abre la ventana de conexión al servidor."""
        self.window_manager.abrir_ventana_conectar()

    def ventana_admin(self) -> None:
        """Abre la ventana de administración."""
        self.window_manager.ventana_admin()

    def ventana_esperar_jugadores(self) -> None:
        """Abre la ventana de espera de jugadores."""
        self.window_manager.ventana_esperar_jugadores()

    def update_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Update the turn and round number display.

        Args:
            num_turno (int): The current turn number
            num_ronda (int): The current round number
            jugador_actual_id (int, optional): ID del jugador actual
            jugador_actual_nombre (str, optional): Nombre del jugador actual
            jugador_actual_color (str, optional): Color del jugador actual

        """
        self.status_manager.update_turno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )

    def update_status_bar(self, text: str, color: str | None = None) -> None:
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
            color (str, optional): Color for the text (e.g., 'green', 'red', '#ff0000')

        """
        self.status_manager.update_status_bar(text, color)

    def update_timer_display(self, text: str, color: str | None = None) -> None:
        """Update the timer display in the status bar.

        Args:
            text (str): The timer text to display
            color (str, optional): Color for the text

        """
        self.status_manager.update_timer_display(text, color)

    def clear_status_bar(self) -> None:
        """Clear the status bar message, but keep the turn number."""
        self.status_manager.clear_status_bar()

    def update_game_state(self, estado: str) -> None:
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state

        """
        self.status_manager.update_game_state(estado)

    def update_mi_jugador_info(self) -> None:
        """Actualiza la información del usuario actual (mi jugador).

        Actualiza la información en la barra de estado.
        """
        self.status_manager.update_mi_jugador_info()

    def update_unidades_disponibles(self, unidades: dict[str, int]) -> None:
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2, "Africa": 3}

        """
        self.units_manager.update_unidades_disponibles(unidades)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Maneja eventos de teclado.

        Args:
            event: Evento de teclado.

        """
        if event.key() in {Qt.Key.Key_Enter, Qt.Key.Key_Return} and self.chat:
            self.chat.send_message()
        elif (
            event.key() == Qt.Key.Key_Escape
            and self.scene
            and hasattr(self.scene, "selection_manager")
        ):
            # Cancelar selección con tecla Escape usando selection_manager
            self.scene.selection_manager.cancelar_seleccion()

    def closeEvent(self, _: QCloseEvent) -> None:  # noqa: N802
        """Maneja el evento de cierre de la ventana.

        Args:
            _: Evento de cierre (no usado).

        """
        self._vivo = False
        # Limpiar recursos del gestor de sonidos
        self.sound_manager.cleanup()

    def finalizar_turno(self) -> None:
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        self.game_actions_manager.finalizar_turno()

    def atacar(self) -> None:
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        self.game_actions_manager.atacar()

    def get_max_attack_units(self, pais: str) -> int:
        """Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)

        """
        return self.game_actions_manager.get_max_attack_units(pais)

    def canjear_misil(self, pais: str) -> None:
        """Canjea unidades por 1 misil en el país especificado.

        Args:
            pais (str): Nombre del país donde canjear el misil

        """
        self.game_actions_manager.canjear_misil(pais)

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen (str): País desde donde se lanza el misil
            pais_destino (str): País objetivo del misil

        """
        self.game_actions_manager.lanzar_misil(pais_origen, pais_destino)

    def set_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Establece la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
            objetivos_secretos (bool): Si los objetivos secretos están activados
            misiles_habilitados (bool): Si el sistema de misiles está habilitado

        """
        self.config_manager.set_configuracion_partida(
            segundos_por_turno,
            paises_para_victoria,
            objetivos_secretos=objetivos_secretos,
            misiles_habilitados=misiles_habilitados,
        )
        # Mantener compatibilidad con código que accede directamente
        self.misiles_habilitados = misiles_habilitados

    def mostrar_configuracion_partida(self) -> None:
        """Muestra la ventana de configuración de la partida."""
        self.config_manager.mostrar_configuracion_partida()

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Establece el objetivo secreto del jugador.

        Args:
            objetivo_id (str): ID del objetivo secreto
            descripcion (str): Descripción del objetivo secreto

        """
        self.config_manager.set_objetivo_secreto(objetivo_id, descripcion)

    def mostrar_tarjetas(self) -> None:
        """Muestra la ventana de tarjetas del jugador."""
        self.card_manager.mostrar_tarjetas()

    def show_battle_result_dialog(
        self,
        batalla_data: dict[str, Any],
        on_finished: Callable[[], None],
    ) -> None:
        """Muestra el diálogo modal con la animación de resultado de batalla.

        Args:
            batalla_data: Datos de la batalla (origen, destino, dados, etc.).
            on_finished: Callback ejecutado al terminar la animación.

        """
        from pyteg.gui.dialogs.dice_animation import (  # noqa: PLC0415
            BattleResultDialog,
        )

        dialog = BattleResultDialog(batalla_data, self)
        dialog.animation_finished.connect(on_finished)
        dialog.exec()
