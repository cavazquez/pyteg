"""Módulo para gestión de idioma en la interfaz gráfica.

Este módulo contiene la clase LanguageManager que maneja toda la lógica
relacionada con el cambio de idioma y la actualización de textos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from pyteg.i18n import translate as _
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol

_LOG = get_logger("gui.language_manager")


class LanguageManager:
    """Gestiona el cambio de idioma y actualización de textos.

    Esta clase se encarga de manejar los cambios de idioma y actualizar
    todos los componentes de la GUI cuando cambia el idioma.
    """

    def __init__(self, main_window: MainWindowProtocol) -> None:
        """Inicializa el gestor de idioma.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def on_language_changed(self, lang_code: str) -> None:
        """Maneja el cambio de idioma actualizando todos los componentes de la GUI.

        Args:
            lang_code: Código del nuevo idioma (ej: 'es', 'en').

        """
        # Actualizar título de la ventana
        map_title = getattr(self.main_window, "map_window_title", None)
        self.main_window.setWindowTitle(
            map_title() if callable(map_title) else _("PyTeg")
        )

        self._refresh_status_and_controls(lang_code)
        self._refresh_selection_and_toolbar(lang_code)

        players_title = getattr(self.main_window, "players_title_label", None)
        if players_title is not None:
            players_title.setText(_("JUGADORES"))

        units_title = getattr(self.main_window, "units_section_title_label", None)
        if units_title is not None:
            units_title.setText(_("UNIDADES"))

        units_manager = getattr(self.main_window, "units_manager", None)
        if units_manager is not None:
            units_manager.refresh_unit_labels()

        # Refrescar cualquier widget top-level visible que exponga
        # `update_language(lang_code)` (duck typing). Esto cubre la ventana de
        # espera de jugadores, el diálogo de tarjetas (si en algún momento se
        # vuelve no-modal), etc., sin acoplar `LanguageManager` a clases concretas.
        for widget in QApplication.topLevelWidgets():
            update = getattr(widget, "update_language", None)
            if (
                callable(update)
                and widget.isVisible()
                and id(widget) != id(self.main_window)
            ):
                update(lang_code)

        # No necesitamos actualizar el selector de idioma porque ya maneja
        # su propio estado

        _LOG.debug("GUI actualizada al idioma: %s", lang_code)

    def _refresh_status_and_controls(self, lang_code: str) -> None:
        """Reconstruye las etiquetas de estado y controles persistentes."""
        status_manager = getattr(self.main_window, "status_manager", None)
        refresh_status = getattr(status_manager, "refresh_language", None)
        if callable(refresh_status):
            refresh_status()
        else:
            # Compatibilidad con hosts mínimos que no montan StatusManager.
            self.main_window.mi_jugador_text.setText(_("Mi jugador:"))

        for name in ("language_selector", "sound_control"):
            widget = getattr(self.main_window, name, None)
            update_language = getattr(widget, "update_language", None)
            if callable(update_language):
                update_language(lang_code)

    def _refresh_selection_and_toolbar(self, lang_code: str) -> None:
        """Reaplica textos de selección y acciones tras el cambio de idioma."""
        # Refrescar el label de selección desde la fuente de verdad
        # (CountrySelectionManager) en vez de comparar cadenas literales.
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager is not None and hasattr(
            selection_manager, "refresh_labels"
        ):
            selection_manager.refresh_labels()

        # Actualizar la toolbar
        if self.main_window.toolbar is not None:
            self.main_window.toolbar.update_language(lang_code)
        self._refresh_gameplay_actions()

    def _refresh_gameplay_actions(self) -> None:
        """Reaplica textos dinámicos de la fase después de cambiar idioma."""
        refresh_actions = getattr(self.main_window, "refresh_gameplay_actions", None)
        if callable(refresh_actions):
            refresh_actions()
