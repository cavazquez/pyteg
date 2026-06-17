"""Diálogo para colocar varias unidades en un país."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import _


class PlaceUnitsDialog(QDialog):
    """Diálogo para elegir cuántas unidades colocar en un país."""

    def __init__(
        self,
        pais: str,
        max_unidades: int,
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa el diálogo de colocación.

        Args:
            pais: País destino.
            max_unidades: Máximo de unidades colocables.
            parent: Widget padre.

        """
        super().__init__(parent)
        self.pais = pais
        self.max_unidades = max(0, max_unidades)
        self.cantidad_seleccionada = (
            min(1, self.max_unidades) if self.max_unidades else 0
        )

        self.setWindowTitle(_("Colocar unidades"))
        self.setFixedSize(380, 200)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(_("Colocar en {}").format(self.pais))
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        layout.addWidget(QLabel(_("Cantidad a colocar:")))

        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1 if self.max_unidades else 0)
        self.spin_box.setMaximum(max(1, self.max_unidades))
        self.spin_box.setValue(self.cantidad_seleccionada or 1)
        self.spin_box.setEnabled(self.max_unidades > 0)
        self.spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin_box)

        buttons = QHBoxLayout()
        cancel = QPushButton(_("Cancelar"))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        place_btn = QPushButton(_("Colocar"))
        place_btn.setDefault(True)
        place_btn.setEnabled(self.max_unidades > 0)
        place_btn.clicked.connect(self.accept)
        buttons.addWidget(place_btn)
        layout.addLayout(buttons)

    def _on_value_changed(self, value: int) -> None:
        self.cantidad_seleccionada = value

    def get_cantidad(self) -> int:
        """Retorna la cantidad seleccionada.

        Returns:
            Unidades a colocar elegidas en el diálogo.

        """
        return self.cantidad_seleccionada or self.spin_box.value()
