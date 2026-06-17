"""Diálogo para seleccionar cuántas unidades mover entre países."""

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


class MoveDialog(QDialog):
    """Diálogo para seleccionar cuántas unidades mover."""

    def __init__(
        self,
        origen: str,
        destino: str,
        max_unidades: int,
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa el diálogo de movimiento.

        Args:
            origen: País de origen.
            destino: País de destino.
            max_unidades: Máximo movible (queda al menos 1 en origen).
            parent: Widget padre.

        """
        super().__init__(parent)
        self.origen = origen
        self.destino = destino
        self.max_unidades = max(0, max_unidades)
        self.cantidad_seleccionada = (
            min(1, self.max_unidades) if self.max_unidades else 0
        )

        self.setWindowTitle(_("Seleccionar Unidades a Mover"))
        self.setFixedSize(400, 220)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title_label = QLabel(_("Mover de {} a {}").format(self.origen, self.destino))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        instruction_label = QLabel(_("Selecciona cuántas unidades mover:"))
        layout.addWidget(instruction_label)

        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1 if self.max_unidades else 0)
        self.spin_box.setMaximum(max(1, self.max_unidades))
        self.spin_box.setValue(self.cantidad_seleccionada or 1)
        self.spin_box.setEnabled(self.max_unidades > 0)
        self.spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin_box)

        button_layout = QHBoxLayout()

        cancel_button = QPushButton(_("Cancelar"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        move_button = QPushButton(_("Mover"))
        move_button.setDefault(True)
        move_button.setEnabled(self.max_unidades > 0)
        move_button.clicked.connect(self.accept)
        button_layout.addWidget(move_button)

        layout.addLayout(button_layout)

    def _on_value_changed(self, value: int) -> None:
        self.cantidad_seleccionada = value

    def get_cantidad_unidades(self) -> int:
        """Retorna la cantidad de unidades seleccionada.

        Returns:
            Cantidad de unidades a mover.

        """
        return self.cantidad_seleccionada or self.spin_box.value()
