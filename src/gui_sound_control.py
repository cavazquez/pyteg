"""
Widget de control de sonido para PyTeg.

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

from src.i18n import translate as _

if TYPE_CHECKING:
    from src.sound_manager import SoundManager


class SoundControlWidget(QWidget):
    """Widget para controlar el volumen y estado de los sonidos."""

    def __init__(
        self,
        sound_manager: SoundManager,
        parent: QWidget | None = None,
    ):
        """
        Inicializa el widget de control de sonido.

        Args:
            sound_manager: Instancia del SoundManager
            parent: Widget padre
        """
        super().__init__(parent)
        self.sound_manager = sound_manager

        # Layout horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        # Botón de mute/unmute
        self.mute_button = QPushButton("🔊")
        self.mute_button.setFixedSize(28, 24)
        self.mute_button.setToolTip(_("Silenciar/Activar sonidos"))
        self.mute_button.clicked.connect(self._toggle_mute)
        self.mute_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        layout.addWidget(self.mute_button)

        # Label de volumen
        self.volume_label = QLabel(_("Vol:"))
        self.volume_label.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(self.volume_label)

        # Slider de volumen
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(sound_manager.get_volume() * 100))
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setToolTip(_("Ajustar volumen"))
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 6px;
                background: #e0e0e0;
                margin: 0px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #5c9fd6;
                border: 1px solid #4a8bc2;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #6bb0e7;
            }
        """)
        layout.addWidget(self.volume_slider)

        # Label de porcentaje
        self.percentage_label = QLabel("50%")
        self.percentage_label.setFixedWidth(35)
        self.percentage_label.setStyleSheet("color: #555; font-size: 11px;")
        self.percentage_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.percentage_label)

        # Actualizar estado inicial
        self._update_display()

    def _toggle_mute(self) -> None:
        """Alterna entre silenciar y activar sonidos."""
        enabled = self.sound_manager.is_enabled()
        self.sound_manager.set_enabled(not enabled)
        self._update_display()

    def _on_volume_changed(self, value: int) -> None:
        """
        Maneja cambios en el slider de volumen.

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
            elif volume < 0.5:
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
