"""Protocolos para tipar el host de la barra de estado.

Permiten que `pyteg.gui.status_bar.builder` mute la `Gui` sin importarla
(evita ciclos) y satisface mypy estricto.
"""

# ruff: noqa: D102

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QStatusBar, QWidget

    from pyteg.gui.widgets.language_selector import LanguageSelector
    from pyteg.gui.widgets.sound_control import SoundControlWidget
    from pyteg.sound_manager import SoundManager


class StatusBarHost(Protocol):
    """Interfaz mínima que debe ofrecer la ventana para construir la barra.

    El builder asigna estos atributos sobre el host; declararlos aquí
    explícitamente le permite a mypy verificar el contrato.
    """

    sound_manager: SoundManager
    theme_manager: Any
    language_manager: Any

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

    def setStatusBar(self, status_bar: QStatusBar) -> Any: ...  # noqa: N802
