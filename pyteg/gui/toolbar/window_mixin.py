"""Ventana principal: tamaño, pantalla completa y zoom del mapa desde la toolbar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from pyteg.gui.toolbar.size import center_window_on_screen
from pyteg.i18n import translate as _

_SPLITTER_PARTS = 2
_HIDDEN_SIZE = 0
_CHAT_RESTORE_SIZE = 120
_SIDEBAR_RESTORE_SIZE = 240

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

    from pyteg.gui.managers.protocols import MainWindowProtocol


class ToolBarWindowMixin:
    """Redimensionado, centrado, fullscreen y reset de vista del mapa."""

    main_window: MainWindowProtocol
    button_fullscreen: QAction | None

    def resize_window(self, width: int, height: int) -> None:
        """Cambia el tamaño de la ventana principal."""
        if width == 0 or height == 0:  # Pantalla completa
            self.main_window.showFullScreen()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(True)
        else:
            self.main_window.showNormal()
            self.main_window.resize(width, height)
            self.center_window()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(False)

    def fit_to_screen(self) -> None:
        """Ajusta la ventana al tamaño de la pantalla con un margen."""
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        self.main_window.showNormal()
        self.main_window.resize(width, height)
        self.center_window()

    def center_window(self) -> None:
        """Centra la ventana en la pantalla."""
        center_window_on_screen(self.main_window)

    def _toggle_fullscreen(self) -> None:
        """Alterna entre pantalla completa y modo normal."""
        if self.main_window.isFullScreen():
            self.main_window.showNormal()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(False)
        else:
            self.main_window.showFullScreen()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(True)

    def _reset_map_zoom(self) -> None:
        """Resetea el zoom del mapa para ajustarlo a la ventana."""
        view = getattr(self.main_window, "view", None)
        if view is not None and hasattr(view, "reset_zoom"):
            view.reset_zoom()
            self.main_window.status_bar.showMessage(
                _("Mapa ajustado al tamaño de la ventana"), 2000
            )

    def toggle_chat(self, visible: bool) -> None:  # noqa: FBT001
        """Muestra u oculta el chat sin destruir su historial."""
        chat = getattr(self.main_window, "chat", None)
        if chat is None:
            return
        chat.setVisible(visible)
        action = getattr(self, "button_toggle_chat", None)
        if action is not None and action.isChecked() != visible:
            action.setChecked(visible)
        if visible:
            splitter = getattr(self.main_window, "vertical_splitter", None)
            if splitter is not None:
                sizes = splitter.sizes()
                if len(sizes) == _SPLITTER_PARTS and sizes[1] == _HIDDEN_SIZE:
                    splitter.setSizes([
                        max(1, sizes[0] - _CHAT_RESTORE_SIZE),
                        _CHAT_RESTORE_SIZE,
                    ])

    def toggle_sidebar(self, visible: bool) -> None:  # noqa: FBT001
        """Muestra u oculta jugadores y unidades para priorizar el mapa."""
        panel = getattr(self.main_window, "right_column_scroll", None)
        if panel is None:
            panel = getattr(self.main_window, "right_column_widget", None)
        if panel is None:
            return
        panel.setVisible(visible)
        action = getattr(self, "button_toggle_sidebar", None)
        if action is not None and action.isChecked() != visible:
            action.setChecked(visible)
        if visible:
            splitter = getattr(self.main_window, "horizontal_splitter", None)
            if splitter is not None:
                sizes = splitter.sizes()
                if len(sizes) == _SPLITTER_PARTS and sizes[1] == _HIDDEN_SIZE:
                    splitter.setSizes([
                        max(1, sizes[0] - _SIDEBAR_RESTORE_SIZE),
                        _SIDEBAR_RESTORE_SIZE,
                    ])
