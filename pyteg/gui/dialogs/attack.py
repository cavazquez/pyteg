"""Módulo para el diálogo de selección de unidades para ataque."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import _, ngettext


class AttackDialog(QDialog):
    """Diálogo para seleccionar con cuántas unidades atacar."""

    def __init__(
        self,
        origen: str,
        destino: str,
        max_unidades: int,
        parent: QWidget | None = None,
    ):
        """Inicializa el diálogo de ataque.

        Args:
            origen (str): Nombre del país atacante
            destino (str): Nombre del país defensor
            max_unidades (int): Máximo número de unidades disponibles para atacar
            parent: Widget padre

        """
        super().__init__(parent)
        self.origen = origen
        self.destino = destino
        self.max_unidades = min(max_unidades, 3)  # Máximo 3 unidades
        self.cantidad_seleccionada: int | None = None

        self.setWindowTitle(_("Seleccionar Unidades de Ataque"))
        self.setFixedSize(400, 280)
        self.setModal(True)

        # Eliminar botones de maximizar y minimizar
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        title_label = QLabel(_("Atacar de {} a {}").format(self.origen, self.destino))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Etiqueta de instrucción
        instruction_label = QLabel(_("Selecciona con cuántas unidades atacar:"))
        layout.addWidget(instruction_label)

        # Grupo de botones de radio para seleccionar cantidad
        self.button_group = QButtonGroup(self)
        radio_layout = QVBoxLayout()

        for i in range(1, self.max_unidades + 1):
            radio_button = QRadioButton(
                ngettext("1 unidad", "{} unidades", i).format(i)
            )
            self.button_group.addButton(radio_button, i)
            radio_layout.addWidget(radio_button)

            # Seleccionar el máximo por defecto
            if i == self.max_unidades:
                radio_button.setChecked(True)
                self.cantidad_seleccionada = i

        layout.addLayout(radio_layout)

        # Conectar señal para actualizar selección
        self.button_group.buttonClicked.connect(self._on_selection_changed)

        # Botones de acción
        button_layout = QHBoxLayout()

        cancel_button = QPushButton(_("Cancelar"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        attack_button = QPushButton(_("Atacar"))
        attack_button.setDefault(True)
        attack_button.clicked.connect(self.accept)
        button_layout.addWidget(attack_button)

        layout.addLayout(button_layout)

    def _on_selection_changed(self, button: QAbstractButton) -> None:
        """Maneja el cambio de selección de cantidad de unidades."""
        self.cantidad_seleccionada = self.button_group.id(button)

    def get_cantidad_unidades(self) -> int:
        """Retorna la cantidad de unidades seleccionada.

        Returns:
            int: Cantidad de unidades seleccionada (1-3)

        """
        return self.cantidad_seleccionada or 1
