"""Módulo para la barra de herramientas de la interfaz gráfica."""

from __future__ import annotations

from typing import Any, cast

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)

from pyteg.gui.toolbar.actions_mixin import ToolBarActionsMixin
from pyteg.gui.toolbar.icons import cargar_icono_toolbar
from pyteg.gui.toolbar.size import (
    create_size_button,
    create_size_menu,
    populate_size_menu,
)
from pyteg.gui.toolbar.window_mixin import ToolBarWindowMixin
from pyteg.i18n import translate as _

_RESPONSIVE_TOOLBAR_WIDTH = 1200


class ToolBar(ToolBarActionsMixin, ToolBarWindowMixin, QToolBar):
    """Barra de herramientas principal de la aplicación."""

    def __init__(self, texto: str, main_window: Any) -> None:
        """Inicializa la barra de herramientas.

        Args:
            texto: Texto de la barra de herramientas.
            main_window: Ventana principal de la aplicación.

        """
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        # Mostrar texto al lado del ícono para mejor legibilidad
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        self.main_window = main_window
        self._observed_window = cast("QObject", main_window)

        # Referencias a los botones que se activan/desactivan
        self.button_conectar: QAction | None = None
        self.button_atacar: QAction | None = None
        self.button_mover: QAction | None = None
        self.button_finalizar_turno: QAction | None = None
        self.button_tarjetas: QAction | None = None
        self.button_fullscreen: QAction | None = None
        self.button_admin: QAction | None = None
        self.button_reset_zoom: QAction | None = None
        self.button_configuracion: QAction | None = None
        self.button_toggle_chat: QAction | None = None
        self.button_toggle_sidebar: QAction | None = None
        self.size_button: QToolButton | None = None
        self._panel_splitters_connected = False
        self.size_menu = create_size_menu(self)

        # Configurar la barra de herramientas
        self._setup_action_buttons()
        self._setup_size_menu()

        # Establecer estado inicial (desconectado)
        self._habilitar_solo_conectar()
        self._observed_window.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        """Mantiene el toggle de fullscreen acorde al estado real de la ventana.

        Returns:
            Si el evento fue procesado por el filtro heredado.

        """
        if (
            watched is self._observed_window
            and event.type() == QEvent.Type.WindowStateChange
        ):
            self._sync_fullscreen_action()
        return super().eventFilter(watched, event)

    def update_language(self, lang_code: str) -> None:
        """Actualiza todos los textos de la toolbar cuando cambia el idioma."""
        # Nota: lang_code se recibe para compatibilidad con la señal Qt
        del lang_code  # Suprimir warning de argumento no usado
        # Actualizar botones principales
        if self.button_tarjetas:
            self.button_tarjetas.setText(_("Tarjetas"))
            self._actualizar_ayuda_tarjetas()
        self._actualizar_accion_conexion(conectado=self._esta_conectado())

        if self.button_atacar:
            self.button_atacar.setText(_("Atacar"))
            self.button_atacar.setToolTip(_("Atacar país seleccionado"))
            self.button_atacar.setStatusTip(
                _("Ejecutar ataque entre países seleccionados")
            )

        if self.button_mover:
            self.button_mover.setText(_("Mover"))
            self.button_mover.setToolTip(_("Mover unidades entre países"))
            self.button_mover.setStatusTip(
                _("Mover 1 unidad entre los países seleccionados")
            )

        if self.button_finalizar_turno:
            self.button_finalizar_turno.setText(_("Finalizar Turno"))
            self.button_finalizar_turno.setToolTip(_("Finalizar tu turno actual"))
            self.button_finalizar_turno.setStatusTip(
                _("Pasar el turno al siguiente jugador")
            )

        if self.button_configuracion:
            self.button_configuracion.setText(_("Configuración"))
            self.button_configuracion.setToolTip(_("Ver configuración de la partida"))
            self.button_configuracion.setStatusTip(
                _("Mostrar duración de turno y objetivo de países")
            )

        if self.button_fullscreen:
            self.button_fullscreen.setText(_("Pantalla Completa"))
            self.button_fullscreen.setToolTip(_("Alternar pantalla completa"))
            self.button_fullscreen.setStatusTip(_("Entrar/salir de pantalla completa"))

        if self.button_reset_zoom:
            self.button_reset_zoom.setText(_("Ajustar Mapa"))
            self.button_reset_zoom.setToolTip(_("Ajustar mapa a la ventana"))
            self.button_reset_zoom.setStatusTip(
                _("Resetear zoom y ajustar mapa al tamaño de la ventana")
            )

        self._update_panel_language()

        self._update_size_menu()
        if self.size_button is not None:
            self.size_button.setToolTip(_("Cambiar tamaño de la ventana"))
            self.size_button.setStatusTip(_("Ajustar o elegir tamaño de ventana"))
            self.size_button.setText(_("Cambiar tamaño de la ventana"))
            self.size_button.setAccessibleName(_("Cambiar tamaño de la ventana"))
            self.size_button.setAccessibleDescription(
                _("Ajustar o elegir tamaño de ventana")
            )
        refresh_actions = getattr(self.main_window, "refresh_gameplay_actions", None)
        if callable(refresh_actions):
            refresh_actions()

    def update_responsive_layout(self, width: int) -> None:
        """Reduce la toolbar a íconos cuando la ventana no tiene ancho suficiente."""
        style = (
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            if width >= _RESPONSIVE_TOOLBAR_WIDTH
            else Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.setToolButtonStyle(style)
        self._connect_panel_splitters()
        self._sync_panel_actions()

    def _connect_panel_splitters(self) -> None:
        """Observa ajustes manuales de los splitters cuando ya están creados."""
        if self._panel_splitters_connected:
            return
        vertical = getattr(self.main_window, "vertical_splitter", None)
        horizontal = getattr(self.main_window, "horizontal_splitter", None)
        if vertical is None or horizontal is None:
            return
        vertical.splitterMoved.connect(self._sync_panel_actions)
        horizontal.splitterMoved.connect(self._sync_panel_actions)
        self._panel_splitters_connected = True

    def _sync_panel_actions(self, *_args: object) -> None:
        """Refleja paneles colapsados o restaurados fuera de la toolbar."""
        chat = getattr(self.main_window, "chat", None)
        vertical = getattr(self.main_window, "vertical_splitter", None)
        if chat is not None and vertical is not None and self.button_toggle_chat:
            sizes = vertical.sizes()
            visible = not chat.isHidden() and len(sizes) > 1 and sizes[1] > 0
            self.button_toggle_chat.setChecked(visible)
        panel = getattr(self.main_window, "right_column_scroll", None)
        horizontal = getattr(self.main_window, "horizontal_splitter", None)
        if panel is not None and horizontal is not None and self.button_toggle_sidebar:
            sizes = horizontal.sizes()
            visible = not panel.isHidden() and len(sizes) > 1 and sizes[1] > 0
            self.button_toggle_sidebar.setChecked(visible)

    def _update_panel_language(self) -> None:
        """Actualiza textos de los toggles de paneles."""
        if self.button_toggle_chat:
            self.button_toggle_chat.setText(_("Chat"))
            self.button_toggle_chat.setToolTip(_("Mostrar u ocultar el chat"))
            self.button_toggle_chat.setStatusTip(_("Mostrar u ocultar el chat"))

        if self.button_toggle_sidebar:
            self.button_toggle_sidebar.setText(_("Panel lateral"))
            self.button_toggle_sidebar.setToolTip(
                _("Mostrar u ocultar jugadores y unidades")
            )
            self.button_toggle_sidebar.setStatusTip(
                _("Mostrar u ocultar jugadores y unidades")
            )

    def _update_size_menu(self) -> None:
        """Actualiza el menú de tamaños con las traducciones actuales."""
        populate_size_menu(self.size_menu, self)

    def _setup_spacers_right(self) -> None:
        """Añade un expansor a la derecha para empujar elementos finales."""
        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.addWidget(right_spacer)

    def _setup_action_buttons(self) -> None:
        """Configura los botones de acción en la barra de herramientas."""
        self._toolbar_add_connection_group()
        self._toolbar_add_game_actions_group()
        self._toolbar_add_view_options_group()

    def _toolbar_add_connection_group(self) -> None:
        icono_conectar = cargar_icono_toolbar("icons/conectar.png", "conectar")
        self.button_conectar = QAction(icono_conectar, _("Conectar"), self)
        self.button_conectar.triggered.connect(self._accion_conexion)
        self.button_conectar.setToolTip(_("Conectar al servidor"))
        self.button_conectar.setStatusTip(_("Abrir ventana de conexión"))
        self.addAction(self.button_conectar)
        self.addSeparator()

    def _toolbar_add_game_actions_group(self) -> None:
        icono_atacar = cargar_icono_toolbar("icons/atacar.png", "atacar")
        self.button_atacar = QAction(icono_atacar, _("Atacar"), self)
        self.button_atacar.triggered.connect(self.main_window.atacar)
        self.button_atacar.setToolTip(_("Atacar país seleccionado"))
        self.button_atacar.setStatusTip(_("Ejecutar ataque entre países seleccionados"))
        self.addAction(self.button_atacar)

        icono_mover = cargar_icono_toolbar("icons/mover.png", "mover")
        self.button_mover = QAction(icono_mover, _("Mover"), self)
        self.button_mover.setEnabled(False)
        self.button_mover.triggered.connect(self._mover_paises_seleccionados)
        self.button_mover.setToolTip(_("Mover unidades entre países"))
        self.button_mover.setStatusTip(
            _("Mover 1 unidad entre los países seleccionados")
        )
        self.addAction(self.button_mover)
        self.addSeparator()

        icono_tarjetas = cargar_icono_toolbar("icons/cards.svg", "tarjetas")
        self.button_tarjetas = QAction(icono_tarjetas, _("Tarjetas"), self)
        self.button_tarjetas.setEnabled(False)
        self.button_tarjetas.triggered.connect(self.main_window.mostrar_tarjetas)
        self.button_tarjetas.setToolTip(_("Ver mis tarjetas"))
        self.button_tarjetas.setStatusTip(_("Mostrar tarjetas asignadas al jugador"))
        self.addAction(self.button_tarjetas)

        icono_finalizar = cargar_icono_toolbar("icons/finish.png", "finalizar turno")
        self.button_finalizar_turno = QAction(
            icono_finalizar, _("Finalizar Turno"), self
        )
        self.button_finalizar_turno.setEnabled(True)
        self.button_finalizar_turno.triggered.connect(self.main_window.finalizar_turno)
        self.button_finalizar_turno.setToolTip(_("Finalizar tu turno actual"))
        self.button_finalizar_turno.setStatusTip(
            _("Pasar el turno al siguiente jugador")
        )
        self.addAction(self.button_finalizar_turno)
        self.addSeparator()

    def _toolbar_add_view_options_group(self) -> None:
        icono_config = cargar_icono_toolbar("icons/settings.svg", "configuración")
        self.button_configuracion = QAction(icono_config, _("Configuración"), self)
        self.button_configuracion.setEnabled(True)
        self.button_configuracion.triggered.connect(
            self.main_window.mostrar_configuracion_partida
        )
        self.button_configuracion.setToolTip(_("Ver configuración de la partida"))
        self.button_configuracion.setStatusTip(
            _("Mostrar duración de turno y objetivo de países")
        )
        self.addAction(self.button_configuracion)

        icono_zoom = cargar_icono_toolbar("icons/fit_map.svg", "resetear zoom")
        self.button_reset_zoom = QAction(icono_zoom, _("Ajustar Mapa"), self)
        self.button_reset_zoom.setEnabled(True)
        self.button_reset_zoom.setShortcut(QKeySequence("Ctrl+0"))
        self.button_reset_zoom.triggered.connect(self._reset_map_zoom)
        self.button_reset_zoom.setToolTip(_("Ajustar mapa a la ventana"))
        self.button_reset_zoom.setStatusTip(
            _("Resetear zoom y ajustar mapa al tamaño de la ventana")
        )
        self.addAction(self.button_reset_zoom)

        icono_chat = cargar_icono_toolbar("icons/chat.svg", "chat")
        self.button_toggle_chat = QAction(icono_chat, _("Chat"), self)
        self.button_toggle_chat.setCheckable(True)
        self.button_toggle_chat.setChecked(True)
        self.button_toggle_chat.triggered.connect(self.toggle_chat)
        self.button_toggle_chat.setToolTip(_("Mostrar u ocultar el chat"))
        self.button_toggle_chat.setStatusTip(_("Mostrar u ocultar el chat"))
        self.addAction(self.button_toggle_chat)

        icono_sidebar = cargar_icono_toolbar("icons/sidebar.svg", "panel lateral")
        self.button_toggle_sidebar = QAction(icono_sidebar, _("Panel lateral"), self)
        self.button_toggle_sidebar.setCheckable(True)
        self.button_toggle_sidebar.setChecked(True)
        self.button_toggle_sidebar.triggered.connect(self.toggle_sidebar)
        self.button_toggle_sidebar.setToolTip(
            _("Mostrar u ocultar jugadores y unidades")
        )
        self.button_toggle_sidebar.setStatusTip(
            _("Mostrar u ocultar jugadores y unidades")
        )
        self.addAction(self.button_toggle_sidebar)

    def _setup_size_menu(self) -> None:
        """Configura el menú de tamaño y su botón."""
        self.size_button = create_size_button(self, self.size_menu)

        # Botón Pantalla Completa (toggle)
        self.button_fullscreen = QAction(self)
        icono_full = cargar_icono_toolbar(
            "icons/fullscreen.png", "pantalla completa (toggle)"
        )
        self.button_fullscreen.setIcon(icono_full)
        self.button_fullscreen.setCheckable(True)
        self.button_fullscreen.setShortcut(QKeySequence("F11"))
        self.button_fullscreen.setText(_("Pantalla Completa"))
        self.button_fullscreen.setToolTip(_("Alternar pantalla completa"))
        self.button_fullscreen.setStatusTip(_("Entrar/salir de pantalla completa"))
        self.button_fullscreen.triggered.connect(self._toggle_fullscreen)
        self.addAction(self.button_fullscreen)

        # Espaciador para empujar controles de tamaño a la derecha
        self._setup_spacers_right()
        # Agregar el botón al extremo derecho
        self.addWidget(self.size_button)
