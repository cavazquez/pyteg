"""Ventana principal: tamaño, pantalla completa y zoom del mapa desde la toolbar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from pyteg.gui.toolbar.size import center_window_on_screen
from pyteg.i18n import translate as _

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
        if hasattr(self.main_window, "w") and self.main_window.w:
            view = self.main_window.w
            if hasattr(view, "reset_zoom"):
                view.reset_zoom()
                self.main_window.status_bar.showMessage(
                    _("Mapa ajustado al tamaño de la ventana"), 2000
                )
