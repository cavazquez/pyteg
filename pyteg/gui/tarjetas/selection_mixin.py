"""Selección de tarjetas, grilla 2x2 y reglas de habilitación del canje."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget

from pyteg.config import (
    CARD_SELECTION_ORANGE_THRESHOLD,
    CARD_WIDGET_HEIGHT,
    CARD_WIDGET_WIDTH,
    CARDS_FOR_EXCHANGE,
    DEFAULT_MAP_THEME,
)
from pyteg.core.cartas.canje import seleccion_valida
from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
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
            placeholder.setFixedSize(CARD_WIDGET_WIDTH, CARD_WIDGET_HEIGHT)
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
        return self._seleccion_valida() or self._puede_realizar_canje_especial()

    def _seleccion_valida(self: TarjetasSelectionHost) -> bool:
        """Evalúa la mano con las equivalencias recibidas del motor.

        Returns:
            True si las cartas representan un canje de unidades generales.

        """
        model = getattr(self.parent(), "client_state_model", None)
        rules = getattr(model, "rules", None) or {}
        cards = [
            TarjetaDePais(
                widget.pais,
                widget.simbolo,
                tipo=self.tarjetas[widget.index].get("tipo", "pais"),
                continente=self.tarjetas[widget.index].get("continente"),
            )
            for widget in self.tarjetas_seleccionadas
        ]
        return seleccion_valida(
            cards,
            equivalencias=rules.get("continent_card_exchanges", {}),
            cantidad_variables=rules.get("cards_for_exchange", CARDS_FOR_EXCHANGE),
        )

    def _puede_realizar_canje_especial(self: TarjetasSelectionHost) -> bool:
        """Verifica si se puede realizar un canje especial (país + tarjeta).

        Returns:
            ``True`` solo con una tarjeta seleccionada; el servidor valida el país.

        """
        return (
            len(self.tarjetas_seleccionadas) == 1
            and self.tarjetas[self.tarjetas_seleccionadas[0].index].get("tipo", "pais")
            == "pais"
        )

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
