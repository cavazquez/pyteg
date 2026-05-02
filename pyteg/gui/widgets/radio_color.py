"""Módulo para el widget de botón de radio con color."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QRadioButton, QWidget


class GuiRadioButtonColor(QRadioButton):
    """Botón de radio personalizado para selección de color."""

    def __init__(
        self,
        label: str,
        parent: QWidget | None,
        main_window: Any,
        color: str,
    ) -> None:
        """Inicializa el botón de radio de color.

        Args:
            label: Etiqueta del botón.
            parent: Widget padre.
            main_window: Ventana principal.
            color: Color asociado al botón (hexadecimal).

        """
        super().__init__(label, parent)
        self._main_window = main_window
        self._color = color
        self.toggled.connect(self.seleccionar_boton)

    def seleccionar_boton(self, checked: bool) -> None:  # noqa: FBT001
        """Maneja la selección del botón.

        Args:
            checked: True si el botón está seleccionado.

        """
        if checked:
            transmisor = getattr(self._main_window, "transmisor", None)
            if transmisor is not None:
                transmisor.seleccionar_color(self._color)

    def activar(self) -> None:
        """Habilita el botón."""
        self.setEnabled(True)

    def desactivar(self) -> None:
        """Deshabilita el botón."""
        self.setEnabled(False)

    def limpiar(self) -> None:
        """Limpia el botón activándolo y vaciando su texto."""
        self.activar()
        self.texto("")

    def texto(self, texto: str) -> None:
        """Establece el texto del botón.

        Args:
            texto: Texto a establecer.

        """
        self.setText(texto)

    def seleccionar(self, texto: str) -> None:
        """Selecciona el botón con un texto y lo desactiva.

        Args:
            texto: Texto a mostrar en el botón.

        """
        self.texto(texto)
        self.desactivar()
