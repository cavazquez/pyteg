"""Widget de control de sonido para PyTeg.

Proporciona controles para ajustar el volumen y activar/desactivar sonidos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

from pyteg.config import VOLUME_MEDIUM_THRESHOLD
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.sound_manager import SoundManager


class SoundControlWidget(QWidget):
    """Widget para controlar el volumen y estado de los sonidos."""

    def __init__(
        self,
        sound_manager: SoundManager,
        parent: QWidget | None = None,
    ):
        """Inicializa el widget de control de sonido.

        Args:
            sound_manager: Instancia del SoundManager
            parent: Widget padre

        """
        super().__init__(parent)
        self.sound_manager = sound_manager
        self._compact = False

        # Layout horizontal
        layout = QHBoxLayout(self)
        self._layout = layout
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        # Botón de mute/unmute
        self.mute_button = QPushButton("🔊")
        self.mute_button.setFixedSize(28, 24)
        self.mute_button.setToolTip(_("Silenciar/Activar sonidos"))
        self.mute_button.clicked.connect(self._toggle_mute)
        layout.addWidget(self.mute_button)

        # Label de volumen
        self.volume_label = QLabel(_("Vol:"))
        layout.addWidget(self.volume_label)

        # Slider de volumen
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(sound_manager.get_volume() * 100))
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setToolTip(_("Ajustar volumen"))
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        layout.addWidget(self.volume_slider)

        # Label de porcentaje
        self.percentage_label = QLabel("50%")
        self.percentage_label.setFixedWidth(35)
        self.percentage_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.percentage_label)

        # Actualizar estado inicial
        self._update_display()

    def set_compact(self, compact: bool) -> None:  # noqa: FBT001
        """Conserva mute visible; el volumen pasa al menú de detalles."""
        if compact == self._compact:
            return
        self._compact = compact
        self.volume_label.setVisible(not compact)
        self.volume_slider.setVisible(not compact)
        self.percentage_label.setVisible(not compact)
        self._layout.setContentsMargins(2 if compact else 4, 0, 2, 0)

    def is_compact(self) -> bool:
        """Indica si el slider está en el menú de detalles.

        Returns:
            ``True`` si el control se muestra en modo compacto.

        """
        return self._compact

    def update_language(self, _lang_code: str) -> None:
        """Traduce de nuevo las ayudas y etiquetas del control."""
        self.mute_button.setToolTip(_("Silenciar/Activar sonidos"))
        self.volume_label.setText(_("Vol:"))
        self.volume_slider.setToolTip(_("Ajustar volumen"))

    def apply_theme(self, theme: str) -> None:
        """Aplica colores con contraste a botón, texto y slider."""
        dark = theme == "dark"
        foreground = "#e6e6e6" if dark else "#333333"
        background = "#3a3f47" if dark else "#f0f0f0"
        hover = "#444b5a" if dark else "#e0e0e0"
        pressed = "#525b6b" if dark else "#d0d0d0"
        border = "#4a5060" if dark else "#cccccc"
        groove = "#5a626e" if dark else "#e0e0e0"
        handle = "#8abaff" if dark else "#5c9fd6"
        self.mute_button.setStyleSheet(
            "QPushButton {"
            f"background-color: {background}; color: {foreground}; "
            f"border: 1px solid {border}; border-radius: 3px; font-size: 14px;"
            "}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
            f"QPushButton:pressed {{ background-color: {pressed}; }}"
        )
        self.volume_label.setStyleSheet(f"color: {foreground}; font-size: 11px;")
        self.percentage_label.setStyleSheet(f"color: {foreground}; font-size: 11px;")
        self.volume_slider.setStyleSheet(
            "QSlider::groove:horizontal {"
            f"border: 1px solid {border}; height: 6px; background: {groove}; "
            "margin: 0px; border-radius: 3px; }"
            "QSlider::handle:horizontal {"
            f"background: {handle}; border: 1px solid {border}; "
            "width: 14px; margin: -4px 0; border-radius: 7px; }"
        )

    def _toggle_mute(self) -> None:
        """Alterna entre silenciar y activar sonidos."""
        enabled = self.sound_manager.is_enabled()
        self.sound_manager.set_enabled(not enabled)
        if not enabled:
            # Al reactivar el audio confirmamos el cambio con un clic breve.
            self.sound_manager.play_button()
        self._update_display()

    def _on_volume_changed(self, value: int) -> None:
        """Maneja cambios en el slider de volumen.

        Args:
            value: Valor del slider (0-100)

        """
        volume = value / 100.0
        self.sound_manager.set_volume(volume)
        self._update_display()

    def _update_display(self) -> None:
        """Actualiza la visualización del estado actual."""
        # Actualizar icono del botón
        if self.sound_manager.is_enabled():
            volume = self.sound_manager.get_volume()
            if volume == 0:
                self.mute_button.setText("🔇")
            elif volume < VOLUME_MEDIUM_THRESHOLD:
                self.mute_button.setText("🔉")
            else:
                self.mute_button.setText("🔊")
        else:
            self.mute_button.setText("🔇")

        # Actualizar porcentaje
        volume_percent = int(self.sound_manager.get_volume() * 100)
        self.percentage_label.setText(f"{volume_percent}%")

        # Habilitar/deshabilitar slider según estado
        self.volume_slider.setEnabled(self.sound_manager.is_enabled())
