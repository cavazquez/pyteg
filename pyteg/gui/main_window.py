"""Módulo principal de la interfaz gráfica del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QMainWindow, QWidget

from pyteg.client.colores.paleta import Colores
from pyteg.client.conexion.transmisor import ClientNullTransmisor
from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.facades.main_window_delegates import MainWindowDelegatesMixin
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
    from PySide6.QtGui import QResizeEvent
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QScrollArea,
        QSplitter,
        QStatusBar,
    )

    from pyteg.client.app import Client
    from pyteg.client.conexion.connection import ConnectionClient
    from pyteg.client.tasks.protocols import LobbyWindowProtocol
    from pyteg.client.tasks.types import TarjetaItem
    from pyteg.gui.dialogs.conectar import VentanaConectar
    from pyteg.gui.managers.protocols import MainWindowProtocol
    from pyteg.gui.mapa.scene import QCustomGraphicsScene
    from pyteg.gui.toolbar import ToolBar
    from pyteg.gui.widgets.chat import Chat
    from pyteg.gui.widgets.language_selector import LanguageSelector
    from pyteg.gui.widgets.sound_control import SoundControlWidget
    from pyteg.gui.widgets.view import QCustomGraphicsView


class Gui(QMainWindow, MainWindowDelegatesMixin):
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
    contexto_partida_label: QLabel
    seleccion_label: QLabel
    language_selector: LanguageSelector
    sound_control: SoundControlWidget
    timer_label: QLabel
    right_column_scroll: QScrollArea
    vertical_splitter: QSplitter
    horizontal_splitter: QSplitter

    layout_manager: LayoutManager
    theme_manager: ThemeManager
    players_manager: PlayersManager
    status_manager: StatusManager
    units_manager: UnitsManager
    game_actions_manager: GameActionsManager
    config_manager: ConfigManager
    card_manager: CardManager
    window_manager: WindowManager
    language_manager: LanguageManager

    row_widgets: dict[str, object]
    last_units: dict[str, object]
    status_temp_label: object

    def __init__(self, client: Client, *, map_theme: str = DEFAULT_MAP_THEME) -> None:
        """Inicializa la ventana principal de la GUI.

        Args:
            client: Cliente del juego.
            map_theme: Tema del mapa que se mostrará al iniciar.

        """
        super().__init__()
        self._gui_init_core_state(client, map_theme)
        self._gui_init_window_and_managers()
        self._gui_init_turn_tracking()
        self.layout_manager.setup_graphics_view()
        build_status_bar(self)
        self.show()

    def _gui_init_core_state(self, client: Client, map_theme: str) -> None:
        self._vivo = True
        self.client: Client = client
        self.theme: str = "light"
        self.map_theme: str = map_theme
        self.client_by_id: dict[int, Client] = {}
        self.transmisor = ClientNullTransmisor()
        self.conexion: ConnectionClient | None = None
        self.client_state_model = None
        self.w: LobbyWindowProtocol | None = None
        self.ventana_conectar: VentanaConectar | None = None
        self.scene: QCustomGraphicsScene | None = None
        self.view: QCustomGraphicsView | None = None
        self.chat: Chat | None = None
        self.toolbar: ToolBar | None = None
        self.tarjetas_jugador: list[TarjetaItem] = []
        self.misiles_habilitados: bool = False
        self.partida_finalizada: bool = False
        self.estado_actual: str = "Desconectado"
        self.fase_actual: str | None = None
        self.unidades_pendientes_servidor: int = 0
        self.client_public_revision: int = -1
        self.client_command_results: dict[str, dict[str, object]] = {}
        self.row_widgets: dict[str, object] = {}
        self.last_units: dict[str, object] = {}
        self.status_temp_label: object = None
        self.players_title_label: object = None
        self.units_section_title_label: object = None

    def _gui_init_window_and_managers(self) -> None:
        self.setWindowTitle(self.map_window_title())
        self.resize(QSize(1280, 800))
        mw = cast("MainWindowProtocol", self)
        self.layout_manager = LayoutManager(mw)
        self.theme_manager = ThemeManager(mw)
        self.players_manager = PlayersManager(mw)
        self.status_manager = StatusManager(mw)
        self.units_manager = UnitsManager(mw)
        self.game_actions_manager = GameActionsManager(mw)
        self.config_manager = ConfigManager(mw)
        self.card_manager = CardManager(mw)
        self.window_manager = WindowManager(mw)
        self.language_manager = LanguageManager(mw)
        self.sound_manager = SoundManager()
        self.setMinimumSize(QSize(720, 480))
        self.setMouseTracking(True)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """Ajusta la toolbar al ancho disponible sin alterar el mapa."""
        super().resizeEvent(event)
        self.layout_manager.update_responsive_layout(self.width(), self.height())
        if self.toolbar is not None:
            self.toolbar.update_responsive_layout(self.width())

    def _gui_init_turn_tracking(self) -> None:
        self.turno_actual: int = 0
        self.jugador_actual_id: int | None = None
        self.jugador_actual_nombre: str | None = None
        self.jugador_actual_color: str | None = None
        self.ultimo_pais_colocado: str | None = None
        self.ultimo_continente_colocado: str | None = None
        self.unidades_antes_colocar: dict[str, int] = {}
        self.colores = Colores()

    def map_window_title(self) -> str:
        """Muestra el mapa activo en el título de la ventana.

        Returns:
            Título traducido con el nombre del mapa.

        """
        if self.map_theme == "classic":
            map_name = _("Clásico")
        elif self.map_theme == "revancha":
            map_name = _("Revancha")
        else:
            map_name = self.map_theme
        return f"{_('PyTeg')} — {map_name}"

    def set_map_theme(self, theme: str) -> None:
        """Cambia el mapa antes de conectar y actualiza la vista y el panel.

        Raises:
            ValueError: Si no hay tema o ya existe una conexión activa.

        """
        if theme == self.map_theme and (
            self.scene is None or self.scene.map_theme == theme
        ):
            return
        if not theme:
            msg = _("Seleccioná un mapa válido")
            raise ValueError(msg)
        if self.conexion is not None and self.conexion.esta_ocupada():
            msg = _("Desconectá la partida antes de cambiar de mapa")
            raise ValueError(msg)

        from pyteg.gui.mapa.scene import QCustomGraphicsScene  # noqa: PLC0415

        new_scene = QCustomGraphicsScene(self, theme=theme)
        old_scene = self.scene
        old_theme = self.map_theme
        self.map_theme = theme
        self.scene = new_scene
        if self.view is not None:
            self.view.setScene(new_scene)
            self.view.resetTransform()
            self.view.reset_zoom()
        self.layout_manager.rebuild_units_panel()
        self.setWindowTitle(self.map_window_title())
        if theme != old_theme:
            self.client.reset_session()
            self.client_by_id.clear()
            self.tarjetas_jugador.clear()
            self.config_manager.set_objetivo_secreto(None, None)
            self.client_state_model = None
            self.client_public_revision = -1
            self.client_command_results.clear()
            self.misiles_habilitados = False
            self.partida_finalizada = False
            self._gui_init_turn_tracking()
            self.players_manager.current_player_name = None
            self.players_manager.update_player_list([])
            self.turno_label.setText(_("Turno: 0"))
            self.timer_label.setText("")
            self.update_game_state("Desconectado")
            self.status_manager.update_mi_jugador_info()
        new_scene.selection_manager.refresh_labels()
        if old_scene is not None:
            old_scene.deleteLater()

    def vivo(self) -> bool:
        """Verifica si la ventana está activa.

        Returns:
            True si la ventana está activa, False en caso contrario.

        """
        return self._vivo
