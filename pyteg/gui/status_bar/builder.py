"""Construcción de la barra de estado de la ventana principal.

Este módulo expone funciones puras (sin estado) que reciben la `Gui` y le
montan los widgets de la barra de estado, asignando los atributos
esperados (`turno_label`, `mi_jugador_widget`, `estado_label`, etc.).

Mantener esta lógica fuera de `main_window.py` permite que la ventana
principal sea una fachada delgada y facilita testear/iterar la barra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from pyteg.gui.status_bar import styles
from pyteg.gui.widgets.language_selector import LanguageSelector
from pyteg.gui.widgets.sound_control import SoundControlWidget
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from PySide6.QtGui import QResizeEvent

    from pyteg.gui.status_bar.protocols import StatusBarHost

_FULL_STATUS_WIDTH = 1800
_WIDE_CONTEXT_WIDTH = 1500
_CONTEXT_WIDTH = 1200
_SELECTION_WIDTH = 900


class _ElidedStatusLabel(QLabel):
    """Recorta avisos largos visualmente y conserva el texto en la ayuda."""

    def __init__(self, *, horizontal_padding: int = 4) -> None:
        super().__init__()
        self._full_text = ""
        self._horizontal_padding = horizontal_padding

    def setText(self, text: str) -> None:  # noqa: N802
        self._full_text = text
        self.setToolTip(text)
        self._refresh_elision()

    def text(self) -> str:
        """Expone el texto completo a gestores y lectores de accesibilidad.

        Returns:
            Texto sin recortar.

        """
        return self._full_text

    def clear(self) -> None:
        """Limpia también el texto completo, usado por el layout adaptable."""
        self.setText("")

    def limit_width(self, maximum: int) -> None:
        """Reserva sólo el ancho útil y trunca lo que no entre."""
        desired = (
            self.fontMetrics().horizontalAdvance(self._full_text)
            + self._horizontal_padding
        )
        width = min(maximum, max(60, desired))
        self.setFixedWidth(width)
        self._refresh_elision(width)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_elision()

    def _refresh_elision(self, width: int | None = None) -> None:
        available = max(
            0, (width or self.contentsRect().width()) - self._horizontal_padding
        )
        super().setText(
            self.fontMetrics().elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, available
            )
        )


def _add_vseparator(status_bar: QStatusBar) -> QFrame:
    """Inserta un separador vertical hundido en la barra de estado.

    Returns:
        Separador agregado a la barra.

    """
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    status_bar.addPermanentWidget(sep)
    return sep


def _add_section(
    main_window: StatusBarHost, name: str, widget: QWidget, *, separator: bool = True
) -> None:
    """Registra un bloque y su separador para el diseño adaptable."""
    main_window.status_bar.addPermanentWidget(widget)
    sep = _add_vseparator(main_window.status_bar) if separator else None
    main_window.status_bar_sections[name] = (widget, sep)


def _build_turn_and_local_player(main_window: StatusBarHost) -> None:
    """Monta los bloques `Turno: N` y `Mi jugador:` en la barra de estado."""
    main_window.jugador_actual_widget = QWidget()
    main_window.jugador_actual_layout = QHBoxLayout(main_window.jugador_actual_widget)
    main_window.jugador_actual_layout.setContentsMargins(4, 0, 4, 0)
    main_window.jugador_actual_layout.setSpacing(6)
    main_window.turno_label = QLabel(_("Turno: 0"))
    main_window.turno_label.setStyleSheet(styles.LABEL_BOLD_STYLE)
    main_window.jugador_actual_layout.addWidget(main_window.turno_label)
    _add_section(main_window, "turn", main_window.jugador_actual_widget)

    main_window.mi_jugador_widget = QWidget()
    main_window.mi_jugador_layout = QHBoxLayout(main_window.mi_jugador_widget)
    main_window.mi_jugador_layout.setContentsMargins(4, 0, 4, 0)
    main_window.mi_jugador_layout.setSpacing(6)
    main_window.mi_jugador_text = QLabel(_("Mi jugador:"))
    main_window.mi_jugador_text.setObjectName("miJugadorText")
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
    _add_section(main_window, "player", main_window.mi_jugador_widget)


def _build_pills_and_controls(main_window: StatusBarHost) -> None:
    """Monta las pills (estado, selección), idioma, sonido y temporizador."""
    main_window.estado_label = QLabel(_("Estado: Desconectado"))
    main_window.estado_label.setObjectName("estadoLabel")
    main_window.estado_label.setProperty("class", "pill")
    _add_section(main_window, "state", main_window.estado_label)

    # La fase de juego tiene un propósito distinto al estado de conexión. Se
    # mantiene en una etiqueta propia para que el contexto no reemplace
    # "Estado: En Juego" y siga siendo legible mientras se actualiza la red.
    main_window.contexto_partida_label = _ElidedStatusLabel(horizontal_padding=24)
    main_window.contexto_partida_label.setObjectName("contextoPartidaLabel")
    main_window.contexto_partida_label.setAccessibleName(_("Contexto de la partida"))
    main_window.contexto_partida_label.setToolTip(
        _("Fase, jugador activo y refuerzos pendientes")
    )
    main_window.contexto_partida_label.setVisible(False)
    _add_section(main_window, "context", main_window.contexto_partida_label)

    main_window.seleccion_label = _ElidedStatusLabel(horizontal_padding=24)
    main_window.seleccion_label.setText(_("Selección: Ninguna"))
    main_window.seleccion_label.setProperty("class", "pill")
    _add_section(main_window, "selection", main_window.seleccion_label)

    main_window.language_selector = LanguageSelector()
    main_window.language_selector.language_changed.connect(
        main_window.language_manager.on_language_changed
    )
    main_window.language_selector.apply_theme(main_window.theme)
    _add_section(main_window, "language", main_window.language_selector)

    main_window.sound_control = SoundControlWidget(main_window.sound_manager)
    main_window.sound_control.apply_theme(main_window.theme)
    _add_section(main_window, "sound", main_window.sound_control)

    main_window.timer_label = QLabel("")
    main_window.timer_label.setObjectName("timerLabel")
    main_window.timer_label.setStyleSheet(styles.TIMER_LABEL_STYLE)
    main_window.timer_label.setMinimumWidth(90)
    _add_section(main_window, "timer", main_window.timer_label, separator=False)

    main_window.status_details_button = QToolButton()
    main_window.status_details_button.setText("⋯")
    main_window.status_details_button.setFixedWidth(28)
    main_window.status_details_button.setPopupMode(
        QToolButton.ToolButtonPopupMode.InstantPopup
    )
    details_menu = QMenu(main_window.status_details_button)
    details_menu.aboutToShow.connect(lambda: _populate_details_menu(main_window))
    main_window.status_details_button.setMenu(details_menu)
    main_window.status_bar.addPermanentWidget(main_window.status_details_button)
    main_window.status_details_button.hide()


def _populate_details_menu(main_window: StatusBarHost) -> None:
    """Permite consultar información oculta y cambiar volumen en modo compacto."""
    menu = main_window.status_details_button.menu()
    if menu is None:
        return
    menu.clear()
    player_label = main_window.mi_jugador_text.text()
    username = main_window.mi_username_label.text()
    player_info = f"{player_label} {username}"
    fields = (
        ("player", player_info),
        ("context", main_window.contexto_partida_label.text()),
        ("selection", main_window.seleccion_label.text()),
    )
    hidden_texts = [
        text
        for name, text in fields
        if text and not main_window.status_bar_sections[name][0].isVisible()
    ]
    if hidden_texts:
        panel = QWidget(menu)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)
        for text in hidden_texts:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setMaximumWidth(420)
            layout.addWidget(label)
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(panel)
        menu.addAction(widget_action)

    if main_window.sound_control.is_compact():
        if not menu.isEmpty():
            menu.addSeparator()
        panel = QWidget(menu)
        volume_layout = QHBoxLayout(panel)
        volume_layout.setContentsMargins(8, 4, 8, 4)
        volume_layout.addWidget(QLabel(_("Vol:")))
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(main_window.sound_control.volume_slider.value())
        volume.setEnabled(main_window.sound_control.volume_slider.isEnabled())
        volume.valueChanged.connect(main_window.sound_control.volume_slider.setValue)
        volume.setMinimumWidth(130)
        volume_layout.addWidget(volume)
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(panel)
        menu.addAction(widget_action)


def update_status_bar_layout(main_window: StatusBarHost, width: int) -> None:
    """Prioriza mensajes, tiempo y controles al reducir el ancho de la ventana."""
    show_all = width >= _FULL_STATUS_WIDTH
    show_context = width >= _CONTEXT_WIDTH
    show_selection = width >= _SELECTION_WIDTH
    compact_controls = not show_all
    visible = {
        "turn": True,
        "player": show_all,
        "state": True,
        "context": show_context and bool(main_window.contexto_partida_label.text()),
        "selection": show_selection,
        "language": True,
        "sound": True,
        "timer": True,
    }
    context_limit = 380 if show_all else 280 if width >= _WIDE_CONTEXT_WIDTH else 200
    selection_limit = 320 if show_all else 300 if width >= _CONTEXT_WIDTH else 240
    if isinstance(main_window.contexto_partida_label, _ElidedStatusLabel):
        main_window.contexto_partida_label.limit_width(context_limit)
    if isinstance(main_window.seleccion_label, _ElidedStatusLabel):
        main_window.seleccion_label.limit_width(selection_limit)
    main_window.language_selector.set_compact(compact_controls)
    main_window.sound_control.set_compact(compact_controls)
    for name, (widget, separator) in main_window.status_bar_sections.items():
        widget.setVisible(visible[name])
        if separator is not None:
            separator.setVisible(visible[name])

    details = [
        f"{main_window.mi_jugador_text.text()} {main_window.mi_username_label.text()}"
        if not visible["player"]
        else "",
        main_window.contexto_partida_label.text() if not visible["context"] else "",
        main_window.seleccion_label.text() if not visible["selection"] else "",
    ]
    main_window.status_details_button.setToolTip("\n".join(filter(None, details)))
    main_window.status_details_button.setAccessibleName(
        main_window.status_details_button.toolTip()
    )
    main_window.status_details_button.setVisible(not show_all)


def build_status_bar(main_window: StatusBarHost) -> None:
    """Construye e instala la barra de estado de la ventana principal.

    Args:
        main_window: Ventana principal a la que se le adjunta la barra.

    """
    main_window.status_bar = QStatusBar()
    main_window.status_bar.setMinimumHeight(30)
    main_window.theme_manager._apply_statusbar_theme()  # noqa: SLF001
    main_window.status_bar_sections = {}
    main_window.status_message_label = _ElidedStatusLabel()
    main_window.status_message_label.setObjectName("statusMessageLabel")
    main_window.status_message_label.setMinimumWidth(0)
    main_window.status_message_label.setSizePolicy(
        QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
    )
    # Un aviso importante debe seguir visible aunque Qt active un statusTip
    # temporal de una acción del menú o de la toolbar.
    main_window.status_bar.addPermanentWidget(main_window.status_message_label, 1)
    _build_turn_and_local_player(main_window)
    _build_pills_and_controls(main_window)
    main_window.setStatusBar(main_window.status_bar)
    update_status_bar_layout(main_window, main_window.width())
