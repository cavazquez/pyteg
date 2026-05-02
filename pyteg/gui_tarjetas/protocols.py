# ruff: noqa: D102 — miembros de `Protocol` son contratos, no implementaciones.

"""Protocols para tipar mixins del diálogo de tarjetas sin import de `dialog`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QLabel, QPushButton

    from pyteg.gui_tarjeta_widget import TarjetaWidget


class TarjetasSelectionHost(Protocol):
    """Contrato mínimo para `TarjetasSelectionMixin` (cumple `TarjetasDialog`)."""

    tarjetas: list[dict[str, str]]
    tarjetas_widgets: list[TarjetaWidget]
    tarjetas_seleccionadas: list[TarjetaWidget]
    label_info_seleccion: QLabel
    button_canje: QPushButton
    button_seleccionar_todas: QPushButton
    button_deseleccionar_todas: QPushButton

    def _on_tarjeta_seleccionada(self, _tarjeta_widget: TarjetaWidget) -> None: ...

    def _actualizar_lista_seleccionadas(self) -> None: ...

    def _actualizar_info_seleccion(self) -> None: ...

    def _actualizar_estado_botones(self) -> None: ...

    def _puede_realizar_canje(self) -> bool: ...

    def _puede_realizar_canje_especial(self) -> bool: ...


class TarjetasExchangeHost(Protocol):
    """Contrato mínimo para `TarjetasExchangeMixin`."""

    tarjetas_seleccionadas: list[TarjetaWidget]

    def _puede_realizar_canje(self) -> bool: ...

    def deseleccionar_todas(self) -> None: ...

    def parent(self) -> QObject | None: ...

    def _get_transmisor(self) -> Any | None: ...
