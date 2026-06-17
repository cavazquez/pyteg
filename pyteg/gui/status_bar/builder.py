"""Construcción de la barra de estado de la ventana principal.

Este módulo expone funciones puras (sin estado) que reciben la `Gui` y le
montan los widgets de la barra de estado, asignando los atributos
esperados (`turno_label`, `mi_jugador_widget`, `estado_label`, etc.).

Mantener esta lógica fuera de `main_window.py` permite que la ventana
principal sea una fachada delgada y facilita testear/iterar la barra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStatusBar,
    QWidget,
)

from pyteg.gui.status_bar import styles
from pyteg.gui.widgets.language_selector import LanguageSelector
from pyteg.gui.widgets.sound_control import SoundControlWidget
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.status_bar.protocols import StatusBarHost


def _add_vseparator(status_bar: QStatusBar) -> None:
    """Inserta un separador vertical hundido en la barra de estado."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    status_bar.addPermanentWidget(sep)


def _build_turn_and_local_player(main_window: StatusBarHost) -> None:
    """Monta los bloques `Turno: N` y `Mi jugador:` en la barra de estado."""
    main_window.jugador_actual_widget = QWidget()
    main_window.jugador_actual_layout = QHBoxLayout(main_window.jugador_actual_widget)
    main_window.jugador_actual_layout.setContentsMargins(4, 0, 4, 0)
    main_window.jugador_actual_layout.setSpacing(6)
    main_window.turno_label = QLabel(_("Turno: 0"))
    main_window.turno_label.setStyleSheet(styles.LABEL_BOLD_STYLE)
    main_window.jugador_actual_layout.addWidget(main_window.turno_label)
    main_window.status_bar.addPermanentWidget(main_window.jugador_actual_widget)
    _add_vseparator(main_window.status_bar)

    main_window.mi_jugador_widget = QWidget()
    main_window.mi_jugador_layout = QHBoxLayout(main_window.mi_jugador_widget)
    main_window.mi_jugador_layout.setContentsMargins(4, 0, 4, 0)
    main_window.mi_jugador_layout.setSpacing(6)
    main_window.mi_jugador_text = QLabel(_("Mi jugador:"))
    main_window.mi_jugador_text.setStyleSheet(styles.LABEL_MUTED_STYLE)
    main_window.mi_jugador_layout.addWidget(main_window.mi_jugador_text)
    main_window.mi_color_indicator = QLabel()
    main_window.mi_color_indicator.setFixedSize(16, 16)
    main_window.mi_color_indicator.setStyleSheet(
        styles.MI_COLOR_INDICATOR_DEFAULT_STYLE
    )
    main_window.mi_jugador_layout.addWidget(main_window.mi_color_indicator)
    main_window.mi_username_label = QLabel(_("[No conectado]"))
    main_window.mi_username_label.setStyleSheet(styles.LABEL_BOLD_STYLE)
    main_window.mi_jugador_layout.addWidget(main_window.mi_username_label)
    main_window.status_bar.addPermanentWidget(main_window.mi_jugador_widget)
    _add_vseparator(main_window.status_bar)


def _build_pills_and_controls(main_window: StatusBarHost) -> None:
    """Monta las pills (estado, selección), idioma, sonido y temporizador."""
    main_window.estado_label = QLabel(_("Estado: Desconectado"))
    main_window.estado_label.setObjectName("estadoLabel")
    main_window.estado_label.setProperty("class", "pill")
    main_window.status_bar.addPermanentWidget(main_window.estado_label)
    _add_vseparator(main_window.status_bar)

    main_window.seleccion_label = QLabel(_("Selección: Ninguna"))
    main_window.seleccion_label.setProperty("class", "pill")
    main_window.status_bar.addPermanentWidget(main_window.seleccion_label)
    _add_vseparator(main_window.status_bar)

    main_window.language_selector = LanguageSelector()
    main_window.language_selector.language_changed.connect(
        main_window.language_manager.on_language_changed
    )
    main_window.status_bar.addPermanentWidget(main_window.language_selector)
    _add_vseparator(main_window.status_bar)

    main_window.sound_control = SoundControlWidget(main_window.sound_manager)
    main_window.status_bar.addPermanentWidget(main_window.sound_control)
    _add_vseparator(main_window.status_bar)

    main_window.timer_label = QLabel("")
    main_window.timer_label.setStyleSheet(styles.TIMER_LABEL_STYLE)
    main_window.timer_label.setMinimumWidth(120)
    main_window.status_bar.addPermanentWidget(main_window.timer_label)

    spacer = QWidget()
    spacer.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred,
    )
    main_window.status_bar.addPermanentWidget(spacer)


def build_status_bar(main_window: StatusBarHost) -> None:
    """Construye e instala la barra de estado de la ventana principal.

    Args:
        main_window: Ventana principal a la que se le adjunta la barra.

    """
    main_window.status_bar = QStatusBar()
    main_window.status_bar.setFixedHeight(26)
    main_window.theme_manager._apply_statusbar_theme()  # noqa: SLF001
    _build_turn_and_local_player(main_window)
    _build_pills_and_controls(main_window)
    main_window.setStatusBar(main_window.status_bar)
