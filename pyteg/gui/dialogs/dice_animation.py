"""Diálogo de animación de dados para mostrar los resultados de batalla."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui.widgets.dice_widget import DiceWidget


class BattleResultDialog(QDialog):
    """Diálogo que muestra la animación de dados y el resultado de batalla."""

    animation_finished = Signal()

    def __init__(
        self,
        batalla_data: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa el diálogo de resultado de batalla.

        Args:
            batalla_data: Diccionario con los datos de la batalla.
            parent: Widget padre (opcional).

        """
        super().__init__(parent)
        self.batalla_data = batalla_data
        self.setWindowTitle("Resultado de Batalla")
        self.setModal(True)
        self.setFixedSize(600, 500)

        # Centrar en la pantalla
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        self._setup_ui()
        self._animation_started = False

    def _setup_ui(self) -> None:
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Configurar elementos principales
        self._setup_title_section(layout)
        self._setup_dice_section(layout)
        self._setup_result_section(layout)
        self._setup_buttons_section(layout)

    def _setup_title_section(self, layout: QVBoxLayout) -> None:
        """Configura la sección de título."""
        # Título de la batalla
        title_label = QLabel(
            f"{self.batalla_data['atacante']} vs {self.batalla_data['defensor']}"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Información de países
        countries_label = QLabel(
            f"{self.batalla_data['origen']} → {self.batalla_data['destino']}"
        )
        countries_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        countries_label.setFont(QFont("Arial", 12))
        countries_label.setStyleSheet("color: #666666;")
        layout.addWidget(countries_label)

    def _setup_dice_section(self, layout: QVBoxLayout) -> None:
        """Configura la sección de dados."""
        # Área de dados
        dice_frame = QFrame()
        dice_frame.setFrameStyle(QFrame.Shape.Box)
        dice_frame.setStyleSheet(
            "QFrame { border: 2px solid #cccccc; "
            "border-radius: 10px; background-color: #f9f9f9; }"
        )
        dice_layout = QVBoxLayout(dice_frame)

        # Dados del atacante
        self._setup_attacker_dice(dice_layout)
        dice_layout.addSpacing(20)

        # Dados del defensor
        self._setup_defender_dice(dice_layout)

        layout.addWidget(dice_frame)

    def _setup_attacker_dice(self, dice_layout: QVBoxLayout) -> None:
        """Configura los dados del atacante."""
        attacker_layout = QHBoxLayout()
        attacker_label = QLabel(f"Atacante ({self.batalla_data['atacante']}):")
        attacker_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        attacker_label.setStyleSheet("color: #d32f2f;")
        attacker_layout.addWidget(attacker_label)
        attacker_layout.addStretch()

        self.attacker_dice: list[DiceWidget] = []
        attacker_dice_layout = QHBoxLayout()
        for value in self.batalla_data["dados_atacante"]:
            dice = DiceWidget(value)
            dice.setStyleSheet("border: 2px solid #d32f2f; border-radius: 8px;")
            self.attacker_dice.append(dice)
            attacker_dice_layout.addWidget(dice)
        attacker_dice_layout.addStretch()

        dice_layout.addLayout(attacker_layout)
        dice_layout.addLayout(attacker_dice_layout)

    def _setup_defender_dice(self, dice_layout: QVBoxLayout) -> None:
        """Configura los dados del defensor."""
        defender_layout = QHBoxLayout()
        defender_label = QLabel(f"Defensor ({self.batalla_data['defensor']}):")
        defender_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        defender_label.setStyleSheet("color: #1976d2;")
        defender_layout.addWidget(defender_label)
        defender_layout.addStretch()

        self.defender_dice: list[DiceWidget] = []
        defender_dice_layout = QHBoxLayout()
        for value in self.batalla_data["dados_defensor"]:
            dice = DiceWidget(value)
            dice.setStyleSheet("border: 2px solid #1976d2; border-radius: 8px;")
            self.defender_dice.append(dice)
            defender_dice_layout.addWidget(dice)
        defender_dice_layout.addStretch()

        dice_layout.addLayout(defender_layout)
        dice_layout.addLayout(defender_dice_layout)

    def _setup_result_section(self, layout: QVBoxLayout) -> None:
        """Configura la sección de resultado."""
        # Área de resultado (inicialmente oculta)
        self.result_frame = QFrame()
        self.result_frame.setFrameStyle(QFrame.Shape.Box)
        self.result_frame.setStyleSheet(
            "QFrame { border: 2px solid #4caf50; border-radius: 10px; "
            "background-color: #e8f5e8; }"
        )
        result_layout = QVBoxLayout(self.result_frame)

        # Resultado de la batalla
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        result_layout.addWidget(self.result_label)

        # Pérdidas
        self.losses_label = QLabel()
        self.losses_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.losses_label.setFont(QFont("Arial", 10))
        result_layout.addWidget(self.losses_label)

        self.result_frame.hide()
        layout.addWidget(self.result_frame)

    def _setup_buttons_section(self, layout: QVBoxLayout) -> None:
        """Configura la sección de botones."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Lanzar Dados")
        self.start_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #4caf50; color: white; "
            "border: none; padding: 10px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.start_button.clicked.connect(self._start_animation)
        button_layout.addWidget(self.start_button)

        self.close_button = QPushButton("Cerrar")
        self.close_button.setFont(QFont("Arial", 10))
        self.close_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; "
            "border: none; padding: 10px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        self.close_button.clicked.connect(self.accept)
        self.close_button.hide()  # Oculto hasta que termine la animación
        button_layout.addWidget(self.close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _start_animation(self) -> None:
        """Inicia la animación de los dados."""
        if self._animation_started:
            return

        self._animation_started = True
        self.start_button.setEnabled(False)
        self.start_button.setText("Lanzando...")

        # Iniciar animación de todos los dados
        all_dice = self.attacker_dice + self.defender_dice
        for dice in all_dice:
            dice.start_animation(2000)  # 2 segundos de animación

        # Mostrar resultado después de la animación
        QTimer.singleShot(2500, self._show_result)

    def _show_result(self) -> None:
        """Muestra el resultado de la batalla."""
        # Determinar el resultado
        perdedores = self.batalla_data["resultado"]["restar"]
        atacante = self.batalla_data["atacante"]
        defensor = self.batalla_data["defensor"]

        # Contar pérdidas
        perdidas_atacante = perdedores.count(atacante)
        perdidas_defensor = perdedores.count(defensor)

        # Texto del resultado
        if self.batalla_data["conquistado"]:
            result_text = f"¡{atacante} conquista {self.batalla_data['destino']}!"
            self.result_label.setStyleSheet("color: #d32f2f;")
        elif perdidas_atacante > perdidas_defensor:
            result_text = f"{defensor} defiende exitosamente"
            self.result_label.setStyleSheet("color: #1976d2;")
        else:
            result_text = "Batalla reñida"
            self.result_label.setStyleSheet("color: #ff9800;")

        self.result_label.setText(result_text)

        # Texto de pérdidas
        losses_text = f"Pérdidas: {atacante} (-{perdidas_atacante}), "
        losses_text += f"{defensor} (-{perdidas_defensor})"
        self.losses_label.setText(losses_text)

        # Mostrar resultado y botón cerrar
        self.result_frame.show()
        self.start_button.hide()
        self.close_button.show()

        # Emitir señal de animación terminada
        self.animation_finished.emit()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Se ejecuta cuando se muestra el diálogo."""
        super().showEvent(event)
        # Auto-iniciar la animación después de un breve delay
        QTimer.singleShot(500, self._start_animation)
