"""Módulo principal de la interfaz gráfica del juego."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QEvent, QSize
from PySide6.QtGui import QStatusTipEvent
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QWidget

from pyteg.client.colores.paleta import Colores
from pyteg.client.conexion.transmisor import ClientNullTransmisor
from pyteg.client.hosting import local_game_addresses
from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui.facades.main_window_delegates import MainWindowDelegatesMixin
from pyteg.gui.garbage_collection import install_gui_collection
from pyteg.gui.managers.cards import CardManager
from pyteg.gui.managers.config import ConfigManager
from pyteg.gui.managers.files import GameFilesManager
from pyteg.gui.managers.game_actions import GameActionsManager
from pyteg.gui.managers.language import LanguageManager
from pyteg.gui.managers.layout import LayoutManager
from pyteg.gui.managers.players import PlayersManager
from pyteg.gui.managers.status import StatusManager
from pyteg.gui.managers.theme import ThemeManager
from pyteg.gui.managers.units import UnitsManager
from pyteg.gui.managers.window import WindowManager
from pyteg.gui.status_bar import build_status_bar
from pyteg.gui.status_bar.builder import update_status_bar_layout
from pyteg.i18n import translate as _
from pyteg.sound_manager import SoundManager

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QResizeEvent
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QScrollArea,
        QSplitter,
        QStatusBar,
        QToolButton,
    )

    from pyteg.client.app import Client
    from pyteg.client.conexion.connection import ConnectionClient
    from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
    from pyteg.client.offline import OfflineConnection
    from pyteg.client.state_model import ClientStateModel
    from pyteg.client.tasks.protocols import LobbyWindowProtocol
    from pyteg.client.tasks.types import TarjetaItem
    from pyteg.gui.dialogs.conectar import VentanaConectar
    from pyteg.gui.managers.protocols import MainWindowProtocol
    from pyteg.gui.mapa.scene import QCustomGraphicsScene
    from pyteg.gui.toolbar import ToolBar
    from pyteg.gui.widgets.chat import Chat
    from pyteg.gui.widgets.language_selector import LanguageSelector
    from pyteg.gui.widgets.situation import SituationBanner
    from pyteg.gui.widgets.sound_control import SoundControlWidget
    from pyteg.gui.widgets.view import QCustomGraphicsView
    from pyteg.server.hosting.runtime import HostRuntime


class Gui(QMainWindow, MainWindowDelegatesMixin):
    """Ventana principal de la interfaz gráfica del juego."""

    status_bar: QStatusBar
    status_bar_sections: dict[str, tuple[QWidget, QFrame | None]]
    status_message_label: QLabel
    status_details_button: QToolButton
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
    situation_banner: SituationBanner | None

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

    def __init__(self, client: Client, *, map_theme: str = DEFAULT_MAP_THEME) -> None:
        """Inicializa la ventana principal de la GUI.

        Args:
            client: Cliente del juego.
            map_theme: Tema del mapa que se mostrará al iniciar.

        """
        super().__init__()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            install_gui_collection(app)
        self._gui_init_core_state(client, map_theme)
        self._gui_init_window_and_managers()
        self._gui_init_turn_tracking()
        self.layout_manager.setup_graphics_view()
        build_status_bar(self)
        self.network_status_label = QLabel(_("Desconectado"), self)
        self.network_status_label.setToolTip(
            _("Anfitrión y destino de la conexión de la partida")
        )
        self.status_bar.addPermanentWidget(self.network_status_label)
        self.invitation_button = QPushButton(_("Copiar invitación"), self)
        self.invitation_button.setToolTip(
            _("Compartí esta invitación con los jugadores que querés admitir")
        )
        self.invitation_button.clicked.connect(self.copy_invitation)
        self.invitation_button.hide()
        self.status_bar.addPermanentWidget(self.invitation_button)
        self.files_manager = GameFilesManager(self)
        if self.toolbar is not None:
            self.toolbar.actualizar_estado_conexion(conectado=False)
        self.setAcceptDrops(True)
        self.show()

    def update_invitation_button(self) -> None:
        """Muestra el enlace sólo cuando esta instancia admite participantes."""
        node = getattr(self.conexion, "node", None)
        hosting = self.host_runtime is not None and self.host_runtime.server is not None
        self.invitation_button.setVisible(node is not None or hosting)
        self.invitation_button.setText(_("Copiar invitación"))

    def copy_invitation(self) -> None:
        """Copia una autorización de ingreso con la identidad del destino."""
        host = local_game_addresses()[0]
        node = getattr(self.conexion, "node", None)
        if node is not None:
            invitation = node.invitation(host)
        elif self.host_runtime is not None and self.host_runtime.server is not None:
            invitation = self.host_runtime.invitation(host)
        else:
            return
        QApplication.clipboard().setText(invitation.encode())
        self.update_status_bar(
            _("Invitación copiada. Compartila con los jugadores de esta sala.")
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        """Acepta un único archivo local de partida, turno o repetición."""
        urls = event.mimeData().urls()
        if (
            len(urls) == 1
            and urls[0].isLocalFile()
            and urls[0]
            .toLocalFile()
            .lower()
            .endswith((".pyteg", ".pyturn", ".pyreplay"))
        ):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        """Abre el archivo soltado con las mismas comprobaciones que el menú."""
        urls = event.mimeData().urls()
        if len(urls) != 1 or not urls[0].isLocalFile():
            return
        try:
            if self.files_manager.open_path(urls[0].toLocalFile(), preview=True):
                event.acceptProposedAction()
                if self.files_manager.start_dialog is not None:
                    self.files_manager.start_dialog.close()
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.update_status_bar(str(error))

    def _gui_init_core_state(self, client: Client, map_theme: str) -> None:
        self._vivo = True
        self.client: Client = client
        self.theme: str = "light"
        self.map_theme: str = map_theme
        self.client_by_id: dict[int, Client] = {}
        self.transmisor: IClientTransmisor = ClientNullTransmisor()
        self.conexion: ConnectionClient | OfflineConnection | None = None
        self.host_runtime: HostRuntime | None = None
        self.network_status = "Desconectado"
        self.client_state_model: ClientStateModel | None = None
        self.w: LobbyWindowProtocol | None = None
        self.ventana_conectar: VentanaConectar | None = None
        self.scene: QCustomGraphicsScene | None = None
        self.view: QCustomGraphicsView | None = None
        self.chat: Chat | None = None
        self.toolbar: ToolBar | None = None
        self.situation_banner = None
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
        self.players_title_label: object = None
        self.units_section_title_label: object = None

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Detiene el anfitrión y la recuperación al cerrar esta ventana."""
        self._vivo = False
        if self.conexion is not None:
            self.conexion.desconectar()
        if self.host_runtime is not None:
            self.host_runtime.close()
            self.host_runtime = None
        self.status_manager.clear_status_bar()
        for widget in self.findChildren(QWidget):
            if widget.isWindow():
                widget.close()
        self.sound_manager.cleanup()
        event.accept()

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
        if hasattr(self, "status_bar_sections"):
            update_status_bar_layout(self, self.width())

    def event(self, event: QEvent) -> bool:
        """Envía ayudas de acciones al canal de menor prioridad del estado.

        Returns:
            ``True`` si se procesó la ayuda; si no, el resultado de Qt.

        """
        if (
            event.type() == QEvent.Type.StatusTip
            and isinstance(event, QStatusTipEvent)
            and hasattr(self, "status_message_label")
        ):
            self.status_manager.update_status_tip(event.tip())
            return True
        return super().event(event)

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
            self.reset_session_state()
        new_scene.selection_manager.refresh_labels()
        if old_scene is not None:
            old_scene.deleteLater()

    def vivo(self) -> bool:
        """Verifica si la ventana está activa.

        Returns:
            True si la ventana está activa, False en caso contrario.

        """
        return self._vivo

    def reset_session_state(self) -> None:
        """Limpia la identidad y los datos visuales antes de entrar a otra sala."""
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
        self.status_manager.update_timer_display("")
        self.update_game_state("Desconectado")
        self.status_manager.update_mi_jugador_info()
