"""Configuración inicial de una partida que intercambia turnos por archivos."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import translate as _


class AsyncSetupDialog(QDialog):
    """Elige mapa y jugadores antes de abrir la configuración de reglas."""

    def __init__(self, theme: str, parent: QWidget | None = None) -> None:
        """Reúne los datos de creación en un único formulario."""
        super().__init__(parent)
        self.setWindowTitle(_("Nueva partida por archivos"))
        self.setMinimumWidth(480)
        self.theme_selector = QComboBox()
        self.theme_selector.addItem(_("Clásico"), "classic")
        self.theme_selector.addItem(_("Revancha"), "revancha")
        self.theme_selector.setCurrentIndex(self.theme_selector.findData(theme))
        self.names = QLineEdit(
            ", ".join(_("Jugador {}").format(index) for index in range(1, 5))
        )
        form = QFormLayout()
        form.addRow(_("Mapa:"), self.theme_selector)
        form.addRow(_("Jugadores:"), self.names)
        hint = QLabel(
            _(
                "Ingresá de 1 a 8 nombres separados por comas. Después podrás "
                "elegir las reglas, los objetivos y las cartas de situaciones. "
                "Los turnos se comparten como archivos y no tienen reloj."
            )
        )
        hint.setWordWrap(True)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)
