"""Módulo para gestión de idioma en la interfaz gráfica.

Este módulo contiene la clase LanguageManager que maneja toda la lógica
relacionada con el cambio de idioma y la actualización de textos.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QApplication

from pyteg.i18n import translate as _
from pyteg.logger import get_logger

_LOG = get_logger("gui.language_manager")


class LanguageManager:
    """Gestiona el cambio de idioma y actualización de textos.

    Esta clase se encarga de manejar los cambios de idioma y actualizar
    todos los componentes de la GUI cuando cambia el idioma.
    """

    def __init__(self, main_window: Any) -> None:
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
        self.main_window.setWindowTitle(_("PyTeg"))

        # Actualizar etiquetas de la barra de estado
        self.main_window.mi_jugador_text.setText(_("Mi jugador:"))

        # Actualizar estados si están en valores por defecto
        if self.main_window.estado_label.text() in {
            "Estado: Esperando jugadores",
            "Estado: Waiting for players",
        }:
            self.main_window.estado_label.setText(_("Estado: Esperando jugadores"))

        if self.main_window.turno_label.text() in {
            "Esperando turno",
            "Waiting for turn",
        }:
            self.main_window.turno_label.setText(_("Esperando turno"))

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

        # Refrescar cualquier widget top-level visible que exponga
        # `update_language(lang_code)` (duck typing). Esto cubre la ventana de
        # espera de jugadores, el diálogo de tarjetas (si en algún momento se
        # vuelve no-modal), etc., sin acoplar `LanguageManager` a clases concretas.
        for widget in QApplication.topLevelWidgets():
            update = getattr(widget, "update_language", None)
            if (
                callable(update)
                and widget.isVisible()
                and widget is not self.main_window
            ):
                update(lang_code)

        # No necesitamos actualizar el selector de idioma porque ya maneja
        # su propio estado

        _LOG.debug("GUI actualizada al idioma: %s", lang_code)
