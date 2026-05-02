"""Módulo para la barra de herramientas de la interfaz gráfica."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QSizePolicy,
    QToolBar,
    QWidget,
)

from pyteg.gui_toolbar_actions import ToolBarActionsMixin
from pyteg.gui_toolbar_icons import cargar_icono_toolbar
from pyteg.gui_toolbar_size import (
    create_size_button,
    create_size_menu,
    populate_size_menu,
)
from pyteg.gui_toolbar_window import ToolBarWindowMixin
from pyteg.i18n import translate as _


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

        # Referencias a los botones que se activan/desactivan
        self.button_conectar: QAction | None = None
        self.button_desconectar: QAction | None = None
        self.button_atacar: QAction | None = None
        self.button_mover: QAction | None = None
        self.button_finalizar_turno: QAction | None = None
        self.button_tarjetas: QAction | None = None
        self.button_fullscreen: QAction | None = None
        self.button_admin: QAction | None = None
        self.button_reset_zoom: QAction | None = None
        self.button_configuracion: QAction | None = None
        self.size_menu = create_size_menu(self)

        # Configurar la barra de herramientas
        self._setup_action_buttons()
        self._setup_size_menu()

        # Establecer estado inicial (desconectado)
        self._habilitar_solo_conectar()

    def update_language(self, lang_code: str) -> None:
        """Actualiza todos los textos de la toolbar cuando cambia el idioma."""
        # Nota: lang_code se recibe para compatibilidad con la señal Qt
        del lang_code  # Suprimir warning de argumento no usado
        # Actualizar botones principales
        if self.button_tarjetas:
            self.button_tarjetas.setText(_("Tarjetas"))
        if self.button_conectar:
            self.button_conectar.setText(_("Conectar"))
            self.button_conectar.setToolTip(_("Conectar al servidor"))
            self.button_conectar.setStatusTip(_("Abrir ventana de conexión"))

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

        self._update_size_menu()

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
        self.button_conectar.triggered.connect(self.main_window.abrir_ventana_conectar)
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

        icono_tarjetas = cargar_icono_toolbar("icons/default_size.png", "tarjetas")
        self.button_tarjetas = QAction(icono_tarjetas, _("Tarjetas"), self)
        self.button_tarjetas.setEnabled(True)
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
        icono_config = cargar_icono_toolbar("icons/resize.png", "configuración")
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

        icono_zoom = cargar_icono_toolbar("icons/default_size.png", "resetear zoom")
        self.button_reset_zoom = QAction(icono_zoom, _("Ajustar Mapa"), self)
        self.button_reset_zoom.setEnabled(True)
        self.button_reset_zoom.triggered.connect(self._reset_map_zoom)
        self.button_reset_zoom.setToolTip(_("Ajustar mapa a la ventana"))
        self.button_reset_zoom.setStatusTip(
            _("Resetear zoom y ajustar mapa al tamaño de la ventana")
        )
        self.addAction(self.button_reset_zoom)

    def _setup_size_menu(self) -> None:
        """Configura el menú de tamaño y su botón."""
        size_button = create_size_button(self, self.size_menu)

        # Botón Pantalla Completa (toggle)
        self.button_fullscreen = QAction(self)
        icono_full = cargar_icono_toolbar(
            "icons/fullscreen.png", "pantalla completa (toggle)"
        )
        self.button_fullscreen.setIcon(icono_full)
        self.button_fullscreen.setCheckable(True)
        self.button_fullscreen.setText(_("Pantalla Completa"))
        self.button_fullscreen.setToolTip(_("Alternar pantalla completa"))
        self.button_fullscreen.setStatusTip(_("Entrar/salir de pantalla completa"))
        self.button_fullscreen.triggered.connect(self._toggle_fullscreen)
        self.addAction(self.button_fullscreen)

        # Espaciador para empujar controles de tamaño a la derecha
        self._setup_spacers_right()
        # Agregar el botón al extremo derecho
        self.addWidget(size_button)
