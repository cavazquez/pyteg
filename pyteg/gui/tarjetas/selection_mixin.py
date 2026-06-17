"""Selección de tarjetas, grilla 2x2 y reglas de habilitación del canje."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget

from pyteg.config import (
    CARD_SELECTION_ORANGE_THRESHOLD,
    CARDS_FOR_EXCHANGE,
    DEFAULT_MAP_THEME,
)
from pyteg.gui.widgets.tarjeta import TarjetaWidget
from pyteg.i18n import translate as _

from . import styles

if TYPE_CHECKING:
    from .protocols import TarjetasSelectionHost


class TarjetasSelectionMixin:
    """Grilla de tarjetas, contador de selección y reglas locales de canje."""

    def _create_tarjetas_area(self: TarjetasSelectionHost) -> QWidget:
        """Crea el área donde se muestran las tarjetas.

        Returns:
            Widget contenedor con la grilla de hasta cuatro tarjetas o placeholders.

        """
        widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tarjetas_widgets.clear()

        map_theme = getattr(self, "map_theme", DEFAULT_MAP_THEME)

        for i, tarjeta in enumerate(self.tarjetas[:4]):
            tarjeta_widget = TarjetaWidget(
                tarjeta["pais"],
                tarjeta["simbolo"],
                i,
                map_theme=map_theme,
            )
            tarjeta_widget.seleccionada.connect(self._on_tarjeta_seleccionada)
            self.tarjetas_widgets.append(tarjeta_widget)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(tarjeta_widget, row, col)

        for i in range(len(self.tarjetas), 4):
            placeholder = QLabel(_("Vacío"))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(styles.STYLE_PLACEHOLDER_VACIO)
            placeholder.setFixedSize(120, 80)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(placeholder, row, col)

        widget.setLayout(grid_layout)
        return widget

    def _create_info_seleccion(self: TarjetasSelectionHost) -> QWidget:
        """Crea el área de información sobre la selección actual.

        Returns:
            Widget con la etiqueta de conteo de tarjetas seleccionadas.

        """
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_info_seleccion = QLabel(_("Seleccionadas: 0"))
        self.label_info_seleccion.setStyleSheet(styles.STYLE_LABEL_INFO_INICIAL)

        layout.addWidget(self.label_info_seleccion)
        widget.setLayout(layout)
        return widget

    def _on_tarjeta_seleccionada(
        self: TarjetasSelectionHost, _tarjeta_widget: TarjetaWidget
    ) -> None:
        """Maneja la selección/deselección de una tarjeta."""
        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def _actualizar_lista_seleccionadas(self: TarjetasSelectionHost) -> None:
        """Actualiza la lista de tarjetas seleccionadas."""
        self.tarjetas_seleccionadas = [
            w for w in self.tarjetas_widgets if w.is_seleccionada()
        ]

    def _actualizar_info_seleccion(self: TarjetasSelectionHost) -> None:
        """Actualiza la información mostrada sobre la selección."""
        cantidad = len(self.tarjetas_seleccionadas)
        self.label_info_seleccion.setText(_("Seleccionadas: %s") % cantidad)

        if cantidad == 0:
            color = "#95a5a6"
        elif cantidad <= CARD_SELECTION_ORANGE_THRESHOLD:
            color = "#f39c12"
        else:
            color = "#27ae60"

        self.label_info_seleccion.setStyleSheet(
            styles.style_label_info_seleccion(color)
        )

    def _actualizar_estado_botones(self: TarjetasSelectionHost) -> None:
        """Actualiza el estado habilitado/deshabilitado de los botones."""
        cantidad_seleccionadas = len(self.tarjetas_seleccionadas)

        self.button_canje.setEnabled(self._puede_realizar_canje())

        total_tarjetas = len(self.tarjetas_widgets)
        self.button_seleccionar_todas.setEnabled(
            cantidad_seleccionadas < total_tarjetas
        )
        self.button_deseleccionar_todas.setEnabled(cantidad_seleccionadas > 0)

    def _puede_realizar_canje(self: TarjetasSelectionHost) -> bool:
        """Determina si se puede realizar un canje con las tarjetas seleccionadas.

        Returns:
            ``True`` si la selección cumple las reglas de canje habilitadas en la UI.

        """
        cantidad = len(self.tarjetas_seleccionadas)

        if cantidad == CARDS_FOR_EXCHANGE:
            simbolos = [tarjeta.simbolo for tarjeta in self.tarjetas_seleccionadas]
            unique_count = len(set(simbolos))
            return unique_count in {1, CARDS_FOR_EXCHANGE}
        if cantidad == 1:
            return self._puede_realizar_canje_especial()

        return False

    def _puede_realizar_canje_especial(self: TarjetasSelectionHost) -> bool:
        """Verifica si se puede realizar un canje especial (país + tarjeta).

        Returns:
            ``True`` solo con una tarjeta seleccionada; el servidor valida el país.

        """
        return len(self.tarjetas_seleccionadas) == 1

    def seleccionar_todas(self: TarjetasSelectionHost) -> None:
        """Selecciona todas las tarjetas disponibles."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(seleccionada=True)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def deseleccionar_todas(self: TarjetasSelectionHost) -> None:
        """Deselecciona todas las tarjetas."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(seleccionada=False)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()
