from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QRadioButton, QWidget


class GuiRadioButtonColor(QRadioButton):
    def __init__(
        self,
        label: str,
        parent: QWidget | None,
        main_window: Any,
        color: str,
    ) -> None:
        super().__init__(label, parent)
        self._main_window = main_window
        self._color = color
        self.toggled.connect(self.seleccionar_boton)

    def seleccionar_boton(self, checked: bool) -> None:  # noqa: FBT001
        if checked:
            transmisor = getattr(self._main_window, "transmisor", None)
            if transmisor is not None:
                transmisor.seleccionar_color(self._color)

    def activar(self) -> None:
        self.setEnabled(True)

    def desactivar(self) -> None:
        self.setEnabled(False)

    def limpiar(self) -> None:
        self.activar()
        self.texto("")

    def texto(self, texto: str) -> None:
        self.setText(texto)

    def seleccionar(self, texto: str) -> None:
        self.texto(texto)
        self.desactivar()
