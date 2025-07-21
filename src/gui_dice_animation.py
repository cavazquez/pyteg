"""
Diálogo de animación de dados para mostrar los resultados de batalla.
"""

import secrets

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiceWidget(QWidget):
    """Widget que representa un dado con animación."""

    def __init__(self, final_value=1, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._current_value = 1
        self._final_value = final_value
        self._is_animating = False
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_step)

    def start_animation(self, duration_ms=2000):
        """Inicia la animación del dado."""
        self._is_animating = True
        self._animation_timer.start(100)  # Cambiar valor cada 100ms

        # Detener animación después del tiempo especificado
        QTimer.singleShot(duration_ms, self._stop_animation)

    def _animate_step(self):
        """Paso de animación - cambia el valor del dado aleatoriamente."""
        if self._is_animating:
            self._current_value = secrets.randbelow(6) + 1
            self.update()

    def _stop_animation(self):
        """Detiene la animación y muestra el valor final."""
        self._is_animating = False
        self._animation_timer.stop()
        self._current_value = self._final_value
        self.update()

    def paintEvent(self, event):  # noqa: N802
        """Dibuja el dado con su valor actual."""
        del event  # Unused parameter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dibujar fondo del dado
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(rect, 8, 8)

        # Dibujar puntos según el valor
        self._draw_dice_dots(painter, rect, self._current_value)

    def _draw_dice_dots(self, painter, rect, value):
        """Dibuja los puntos del dado según su valor."""
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(Qt.NoPen)

        dot_size = 6
        center_x = rect.center().x()
        center_y = rect.center().y()
        offset = 12

        # Posiciones de los puntos
        positions = {
            1: [(center_x, center_y)],
            2: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y + offset),
            ],
            3: [
                (center_x - offset, center_y - offset),
                (center_x, center_y),
                (center_x + offset, center_y + offset),
            ],
            4: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
            5: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x, center_y),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
            6: [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x - offset, center_y),
                (center_x + offset, center_y),
                (center_x - offset, center_y + offset),
                (center_x + offset, center_y + offset),
            ],
        }

        # Dibujar los puntos
        for x, y in positions.get(value, []):
            painter.drawEllipse(
                x - dot_size // 2, y - dot_size // 2, dot_size, dot_size
            )


class BattleResultDialog(QDialog):
    """Diálogo que muestra la animación de dados y el resultado de batalla."""

    animation_finished = Signal()

    def __init__(self, batalla_data, parent=None):
        super().__init__(parent)
        self.batalla_data = batalla_data
        self.setWindowTitle("Resultado de Batalla")
        self.setModal(True)
        self.setFixedSize(500, 400)

        # Centrar en la pantalla
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        self._setup_ui()
        self._animation_started = False

    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Configurar elementos principales
        self._setup_title_section(layout)
        self._setup_dice_section(layout)
        self._setup_result_section(layout)
        self._setup_buttons_section(layout)

    def _setup_title_section(self, layout):
        """Configura la sección de título."""
        # Título de la batalla
        title_label = QLabel(
            f"{self.batalla_data['atacante']} vs {self.batalla_data['defensor']}"
        )
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)

        # Información de países
        countries_label = QLabel(
            f"{self.batalla_data['origen']} → {self.batalla_data['destino']}"
        )
        countries_label.setAlignment(Qt.AlignCenter)
        countries_label.setFont(QFont("Arial", 12))
        countries_label.setStyleSheet("color: #666666;")
        layout.addWidget(countries_label)

    def _setup_dice_section(self, layout):
        """Configura la sección de dados."""
        # Área de dados
        dice_frame = QFrame()
        dice_frame.setFrameStyle(QFrame.Box)
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

    def _setup_attacker_dice(self, dice_layout):
        """Configura los dados del atacante."""
        attacker_layout = QHBoxLayout()
        attacker_label = QLabel(f"Atacante ({self.batalla_data['atacante']}):")
        attacker_label.setFont(QFont("Arial", 10, QFont.Bold))
        attacker_label.setStyleSheet("color: #d32f2f;")
        attacker_layout.addWidget(attacker_label)
        attacker_layout.addStretch()

        self.attacker_dice = []
        attacker_dice_layout = QHBoxLayout()
        for value in self.batalla_data["dados_atacante"]:
            dice = DiceWidget(value)
            dice.setStyleSheet("border: 2px solid #d32f2f; border-radius: 8px;")
            self.attacker_dice.append(dice)
            attacker_dice_layout.addWidget(dice)
        attacker_dice_layout.addStretch()

        dice_layout.addLayout(attacker_layout)
        dice_layout.addLayout(attacker_dice_layout)

    def _setup_defender_dice(self, dice_layout):
        """Configura los dados del defensor."""
        defender_layout = QHBoxLayout()
        defender_label = QLabel(f"Defensor ({self.batalla_data['defensor']}):")
        defender_label.setFont(QFont("Arial", 10, QFont.Bold))
        defender_label.setStyleSheet("color: #1976d2;")
        defender_layout.addWidget(defender_label)
        defender_layout.addStretch()

        self.defender_dice = []
        defender_dice_layout = QHBoxLayout()
        for value in self.batalla_data["dados_defensor"]:
            dice = DiceWidget(value)
            dice.setStyleSheet("border: 2px solid #1976d2; border-radius: 8px;")
            self.defender_dice.append(dice)
            defender_dice_layout.addWidget(dice)
        defender_dice_layout.addStretch()

        dice_layout.addLayout(defender_layout)
        dice_layout.addLayout(defender_dice_layout)

    def _setup_result_section(self, layout):
        """Configura la sección de resultado."""
        # Área de resultado (inicialmente oculta)
        self.result_frame = QFrame()
        self.result_frame.setFrameStyle(QFrame.Box)
        self.result_frame.setStyleSheet(
            "QFrame { border: 2px solid #4caf50; border-radius: 10px; "
            "background-color: #e8f5e8; }"
        )
        result_layout = QVBoxLayout(self.result_frame)

        # Resultado de la batalla
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_layout.addWidget(self.result_label)

        # Pérdidas
        self.losses_label = QLabel()
        self.losses_label.setAlignment(Qt.AlignCenter)
        self.losses_label.setFont(QFont("Arial", 10))
        result_layout.addWidget(self.losses_label)

        self.result_frame.hide()
        layout.addWidget(self.result_frame)

    def _setup_buttons_section(self, layout):
        """Configura la sección de botones."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Lanzar Dados")
        self.start_button.setFont(QFont("Arial", 10, QFont.Bold))
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

    def _start_animation(self):
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

    def _show_result(self):
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

    def showEvent(self, event):  # noqa: N802
        """Se ejecuta cuando se muestra el diálogo."""
        super().showEvent(event)
        # Auto-iniciar la animación después de un breve delay
        QTimer.singleShot(500, self._start_animation)
