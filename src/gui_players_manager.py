"""
Módulo para gestión de jugadores en la interfaz gráfica.

Este módulo contiene la clase PlayersManager que maneja toda la lógica
relacionada con la visualización y gestión de la lista de jugadores
en la interfaz gráfica principal.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class PlayersManager:
    """
    Gestiona la visualización y actualización de la lista de jugadores.

    Esta clase se encarga de crear, actualizar y mantener los widgets
    que muestran la información de los jugadores en la interfaz.
    """

    def __init__(self, main_window):
        """
        Inicializa el gestor de jugadores.

        Args:
            main_window: Referencia a la ventana principal (Gui)
        """
        self.main_window = main_window
        self.player_labels = []

    def update_player_list(self, players):
        """
        Updates the player list on the right column.
        Only shows players that are actually playing.
        :param players: List of tuples (name, color) where color is a QColor.
        """
        # Limpiar widgets existentes
        self._clear_player_widgets()

        # Crear widgets solo para jugadores activos
        for name, color in players:
            self._create_single_player_widget(name, color)

    def _clear_player_widgets(self):
        """Elimina todos los widgets de jugadores existentes"""
        if hasattr(self, "player_labels"):
            for _label, _turn_indicator, player_widget in self.player_labels:
                player_widget.setParent(None)
                player_widget.deleteLater()
        self.player_labels = []

    def _create_single_player_widget(self, name, color):
        """Crea un widget individual para un jugador"""
        # Crear un widget para el jugador (estilo tarjeta, neutro)
        player_widget = QFrame()
        player_widget.setObjectName("playerCard")

        player_layout = QHBoxLayout(player_widget)
        player_layout.setContentsMargins(8, 8, 8, 8)
        player_layout.setSpacing(8)

        # Indicador de color (círculo + glifo inicial)
        turn_indicator = self._make_circle_icon(color.name(), None)
        player_layout.addWidget(turn_indicator)

        # Etiqueta con el nombre del jugador
        label = QLabel(name)
        player_layout.addWidget(label)

        # Estilos unificados con sección UNIDADES
        label.setStyleSheet("color: #333; font-weight: 600; font-size: 13px;")

        # Guardar referencia
        self.player_labels.append((label, turn_indicator, player_widget))

        # Añadir al layout
        self.main_window.players_layout.addWidget(player_widget)

        # Aplicar estilo de tarjeta mediante tema
        self.main_window.theme_manager._apply_players_theme(player_widget)  # noqa: SLF001

    def _make_circle_icon(self, color_hex: str, glyph: str | None) -> QLabel:
        """Crea un QLabel con un QPixmap de círculo y opcional glifo."""

        size = 16
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(QColor(color_hex))
        painter.drawEllipse(0, 0, size - 1, size - 1)
        if glyph:
            painter.setPen(QColor("white"))
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pm.rect(), Qt.AlignCenter, glyph)
        painter.end()
        label = QLabel()
        label.setPixmap(pm)
        return label
