"""Widget reutilizable para una tarjeta de país en la mano del jugador."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.core.theme_resources import get_card_image_path


class TarjetaWidget(QWidget):
    """Widget que representa una tarjeta individual."""

    seleccionada = Signal(object)  # Señal emitida cuando se selecciona/deselecciona

    def __init__(
        self,
        pais: str,
        simbolo: str,
        index: int = 0,
        *,
        map_theme: str = DEFAULT_MAP_THEME,
    ) -> None:
        """Inicializa el widget de tarjeta.

        Args:
            pais: Nombre del país de la tarjeta.
            simbolo: Símbolo de la tarjeta (Galeon, Globo, Canon, Comodin).
            index: Índice de la tarjeta (por defecto 0).
            map_theme: Tema de mapa para resolver la imagen del símbolo.

        """
        super().__init__()
        self.pais = pais
        self.simbolo = simbolo
        self.index = index
        self.map_theme = map_theme
        self._seleccionada = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del widget de tarjeta."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_pais = QLabel(self.pais)
        self.label_pais.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_pais.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

        self.label_simbolo = QLabel()
        self.label_simbolo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        imagen_path = get_card_image_path(self.map_theme, self.simbolo)
        if imagen_path:
            pixmap = QPixmap(imagen_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.label_simbolo.setPixmap(scaled_pixmap)
            else:
                self.label_simbolo.setText(self.simbolo)
        else:
            self.label_simbolo.setText(self.simbolo)

        self.label_simbolo.setStyleSheet("""
            QLabel {
                padding: 8px;
                margin-top: 5px;
            }
        """)

        layout.addWidget(self.label_pais)
        layout.addWidget(self.label_simbolo)
        self.setLayout(layout)

        self._actualizar_estilo()
        self.setFixedSize(120, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _actualizar_estilo(self) -> None:
        """Actualiza el estilo según el estado de selección."""
        if self._seleccionada:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: #e8f5e8;
                    border: 3px solid #27ae60;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #229954;
                    background-color: #d5f4d5;
                }
            """)
        else:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: white;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #2980b9;
                    background-color: #ecf0f1;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Maneja el clic en la tarjeta para seleccionar/deseleccionar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_seleccion()
        super().mousePressEvent(event)

    def toggle_seleccion(self) -> None:
        """Alterna el estado de selección de la tarjeta."""
        self._seleccionada = not self._seleccionada
        self._actualizar_estilo()
        self.seleccionada.emit(self)

    def set_seleccionada(self, *, seleccionada: bool) -> None:
        """Establece el estado de selección de la tarjeta."""
        if self._seleccionada != seleccionada:
            self._seleccionada = seleccionada
            self._actualizar_estilo()

    def is_seleccionada(self) -> bool:
        """Retorna True si la tarjeta está seleccionada.

        Returns:
            True si la tarjeta está seleccionada, False en caso contrario.

        """
        return self._seleccionada
