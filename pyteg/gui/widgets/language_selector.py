"""Módulo para el selector de idioma de la interfaz."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from pyteg.i18n import (
    get_available_languages,
    get_current_language,
    set_language,
)
from pyteg.i18n import (
    translate as _,
)
from pyteg.logger import get_logger

_LOG = get_logger("gui.language_selector")

if TYPE_CHECKING:
    from collections.abc import Sequence


class LanguageSelector(QWidget):
    """Widget selector de idioma."""

    # Señal emitida cuando cambia el idioma
    language_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inicializa el selector de idioma.

        Args:
            parent: Widget padre (opcional).

        """
        super().__init__(parent)
        self.combo = QComboBox()
        self._compact = False
        self.setup_ui()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario del selector de idioma."""
        layout = QHBoxLayout(self)
        self._layout = layout
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Label
        self.label = QLabel(_("Idioma:"))
        layout.addWidget(self.label)

        # ComboBox
        self.combo.setMinimumWidth(100)  # Ancho mínimo
        self.combo.setFixedHeight(22)  # Altura fija para consistencia

        self.combo.currentTextChanged.connect(self.on_language_changed)
        layout.addWidget(self.combo)

        # Cargar idiomas disponibles
        self.load_languages()

    def set_compact(self, compact: bool) -> None:  # noqa: FBT001
        """Deja visible el selector, pero reduce el espacio que ocupa."""
        if compact == self._compact:
            return
        self._compact = compact
        self.label.setVisible(not compact)
        self._layout.setContentsMargins(2 if compact else 8, 2, 2, 2)
        self.combo.setMinimumWidth(86 if compact else 100)
        self.combo.setMaximumWidth(96 if compact else 16777215)
        self.combo.setToolTip(_("Idioma:"))

    def update_language(self, _lang_code: str) -> None:
        """Actualiza etiqueta y ayuda después de cambiar el idioma."""
        self.label.setText(_("Idioma:"))
        self.combo.setToolTip(_("Idioma:"))

    def apply_theme(self, theme: str) -> None:
        """Mantiene legibles selector y lista en tema claro y oscuro."""
        dark = theme == "dark"
        foreground = "#e6e6e6" if dark else "#333333"
        background = "#252a33" if dark else "#ffffff"
        border = "#4a5060" if dark else "#cccccc"
        focus = "#8abaff" if dark else "#4361ee"
        self.label.setStyleSheet(f"color: {foreground}; font-weight: 500;")
        self.combo.setStyleSheet(
            "QComboBox {"
            f"background-color: {background}; color: {foreground}; "
            f"border: 1px solid {border}; border-radius: 4px; "
            "padding: 2px 4px; font-size: 12px; }"
            f"QComboBox:hover, QComboBox:focus {{ border-color: {focus}; }}"
            "QComboBox::drop-down { border: none; width: 18px; }"
            "QComboBox QAbstractItemView {"
            f"background-color: {background}; color: {foreground}; "
            f"border: 1px solid {border}; "
            f"selection-background-color: {focus}; "
            f"selection-color: {'#1e1f23' if dark else '#ffffff'}; }}"
        )

    def load_languages(self) -> None:
        """Carga los idiomas disponibles en el combo."""
        languages: Sequence[str] = get_available_languages()
        current_lang = get_current_language()

        language_names: dict[str, str] = {"es": "Español", "en": "English"}

        # Bloquear señales temporalmente para evitar bucles
        self.combo.blockSignals(True)  # noqa: FBT003

        self.combo.clear()
        for lang in languages:
            display_name = language_names.get(lang, lang.upper())
            self.combo.addItem(display_name, lang)

            if lang == current_lang:
                self.combo.setCurrentText(display_name)

        # Reactivar señales
        self.combo.blockSignals(False)  # noqa: FBT003

    def on_language_changed(self, display_name: str) -> None:
        """Maneja el cambio de idioma."""
        lang_code: str | None = None
        for i in range(self.combo.count()):
            if self.combo.itemText(i) == display_name:
                lang_code = self.combo.itemData(i)
                break

        if lang_code and lang_code != get_current_language():
            set_language(lang_code)
            # Emitir señal para que toda la GUI se actualice
            self.language_changed.emit(lang_code)
            _LOG.debug("Idioma cambiado a: %s", lang_code)
        # Si el idioma es el mismo, no hacer nada para evitar bucles
