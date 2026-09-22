"""Etiquetas accesibles y adaptables para los países del mapa."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget


_DISPLAY_NAMES = {
    "GranBretana": "Gran Bretaña",
    "NuevaYork": "Nueva York",
    "Sudafrica": "Sudáfrica",
    "EstadosUnidos": "Estados Unidos",
    "EuropaOccidental": "Europa Occidental",
    "EuropaOriental": "Europa Oriental",
    "MedioOriente": "Medio Oriente",
    "NorteDeAfrica": "Norte de África",
}


def display_country_name(name: str) -> str:
    """Devuelve un nombre legible sin cambiar la clave del mapa.

    Returns:
        Nombre mostrado en la etiqueta.

    """
    if name in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[name]
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name)


def abbreviated_country_name(name: str) -> str:
    """Genera una etiqueta corta para escalas donde el mapa es compacto.

    Returns:
        Abreviatura para una vista alejada.

    """
    words = display_country_name(name).split()
    if len(words) == 1:
        return words[0][:5]
    return "".join(word[0] for word in words[:3]).upper()


class CountryLabel(QGraphicsTextItem):
    """Texto de un país que permanece legible al cambiar el zoom.

    El texto ignora la transformación de la vista: su tamaño en pantalla es
    estable y no se convierte en una mancha ilegible al alejar el mapa. En
    escalas muy pequeñas se oculta para evitar una nube de etiquetas; el
    país vuelve a mostrar su nombre completo cuando recibe foco o selección.
    """

    _MIN_LABEL_SCALE = 0.68
    _FULL_NAME_SCALE = 0.95

    def __init__(self, country_name: str, parent: QGraphicsItem) -> None:
        """Crea la etiqueta como hija del sprite del país."""
        super().__init__(parent=parent)
        self.country_name = country_name
        self.full_name = display_country_name(country_name)
        self.short_name = abbreviated_country_name(country_name)
        self._hovered = False
        self._selected = False
        self._scale = 1.0
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setAcceptHoverEvents(False)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            enabled=True,
        )
        self.setZValue(2_000)
        self.setDefaultTextColor(QColor("#263238"))
        self.setFont(QFont("Sans Serif", 8, QFont.Weight.DemiBold))
        self.setToolTip(self.full_name)
        self._refresh_text()

    def set_zoom_scale(self, scale: float) -> None:
        """Actualiza visibilidad y abreviatura según la escala de la vista."""
        self._scale = max(0.01, scale)
        self._refresh_text()

    def set_hovered(self, hovered: bool) -> None:  # noqa: FBT001
        """Fuerza el nombre completo mientras el cursor está sobre el país."""
        self._hovered = hovered
        self._refresh_text()

    def set_selected(self, selected: bool) -> None:  # noqa: FBT001
        """Fuerza el nombre completo mientras el país está seleccionado."""
        self._selected = selected
        self._refresh_text()

    def _refresh_text(self) -> None:
        focused = self._hovered or self._selected
        visible = focused or self._scale >= self._MIN_LABEL_SCALE
        self.setVisible(visible)
        text = (
            self.full_name
            if focused or self._scale >= self._FULL_NAME_SCALE
            else self.short_name
        )
        self.setPlainText(text)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Pinta una placa translúcida para separar el nombre del mapa."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawRoundedRect(self.boundingRect().adjusted(-2, -1, 2, 1), 2, 2)
        painter.restore()
        super().paint(painter, option, cast("QWidget", widget))
