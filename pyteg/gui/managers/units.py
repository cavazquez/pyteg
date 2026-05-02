"""Módulo para gestión de unidades en la interfaz gráfica.

Este módulo contiene la clase UnitsManager que maneja toda la lógica
relacionada con la visualización y actualización de las unidades disponibles
en la interfaz gráfica principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class UnitsManager:
    """Gestiona la visualización y actualización de unidades disponibles.

    Esta clase se encarga de actualizar el panel de unidades, aplicar estilos
    visuales y gestionar los efectos de cambio (flash) cuando las unidades cambian.
    """

    def __init__(self, main_window: MainWindowProtocol) -> None:
        """Inicializa el gestor de unidades.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def update_unidades_disponibles(self, unidades: dict[str, int]) -> None:  # noqa: PLR0912
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2, "Africa": 3}

        """
        # Mapeo de nombres de continentes del servidor a los de la GUI
        continent_mapping = {
            "Africa": "África",
            "Europa": "Europa",
            "Asia": "Asia",
            "América del Sur": "América del Sur",
            "América del Norte": "América del Norte",
            "Oceanía": "Oceanía",
        }

        # Actualizar unidades generales (infantería)
        if "infanteria" in unidades:
            cantidad = unidades["infanteria"]
            prev = self.main_window.last_units.get("Generales", None)
            # Estilo con color verde si hay unidades disponibles
            if cantidad > 0:
                style = (
                    "font-weight: bold; "
                    "color: #2E7D32; "
                    "background-color: #E8F5E8; "
                    "padding: 4px 8px; "
                    "border-radius: 4px; "
                    "border-left: 3px solid #4CAF50;"
                )
                text = f"Generales: {cantidad}"
            else:
                style = "font-weight: bold; color: #666666;"
                text = f"Generales: {cantidad}"

            self.main_window.value_labels["Generales"].setText(text)
            self.main_window.value_labels["Generales"].setStyleSheet(style)
            if prev is None or prev != cantidad:
                self._flash_row("Generales")
            self.main_window.last_units["Generales"] = cantidad

        # Actualizar unidades de continentes
        for server_name, gui_name in continent_mapping.items():
            if server_name in unidades and gui_name in self.main_window.value_labels:
                cantidad = unidades[server_name]
                prev = self.main_window.last_units.get(gui_name, None)
                if cantidad > 0:
                    # Estilo destacado para continentes con unidades disponibles
                    style = (
                        "font-weight: bold; "
                        "color: #1565C0; "
                        "background-color: #E3F2FD; "
                        "padding: 4px 8px; "
                        "border-radius: 4px; "
                        "border-left: 3px solid #2196F3;"
                    )
                    text = f"{gui_name}: {cantidad}"
                else:
                    # Estilo normal para continentes sin unidades
                    style = "font-weight: bold; color: #666666;"
                    text = f"{gui_name}: 0"

                self.main_window.value_labels[gui_name].setText(text)
                self.main_window.value_labels[gui_name].setStyleSheet(style)
                if prev is None or prev != cantidad:
                    self._flash_row(gui_name)
                self.main_window.last_units[gui_name] = cantidad
            elif gui_name in self.main_window.value_labels:
                # Resetear continentes que no tienen unidades disponibles
                self.main_window.value_labels[gui_name].setText(f"{gui_name}: 0")
                self.main_window.value_labels[gui_name].setStyleSheet(
                    "font-weight: bold; color: #666666;"
                )

        # Actualizar Misiles: usar fila existente y mostrar/ocultar
        if "misiles" in unidades and unidades["misiles"] > 0:
            text = f"Misiles: {unidades['misiles']}"
            style = (
                "font-weight: bold; "
                "color: #D32F2F; "
                "background-color: #FFEBEE; "
                "padding: 4px 8px; "
                "border-radius: 4px; "
                "border-left: 3px solid #F44336;"
            )
            self.main_window.value_labels["Misiles"].setText(text)
            self.main_window.value_labels["Misiles"].setStyleSheet(style)
            # Mostrar fila completa (parent del label)
            self.main_window.row_widgets["Misiles"].setVisible(True)
            prev = self.main_window.last_units.get("Misiles", None)
            if prev is None or prev != unidades["misiles"]:
                self._flash_row("Misiles")
            self.main_window.last_units["Misiles"] = unidades["misiles"]
        else:
            # Ocultar y resetear
            self.main_window.value_labels["Misiles"].setText("Misiles: 0")
            self.main_window.value_labels["Misiles"].setStyleSheet(
                "font-weight: bold; color: #666666;"
            )
            self.main_window.row_widgets["Misiles"].setVisible(False)
            self.main_window.last_units["Misiles"] = 0

    def _flash_row(self, key: str) -> None:
        """Aplica un efecto de flash a una fila de unidades cuando cambia el valor."""
        if key in self.main_window.row_widgets:
            widget = self.main_window.row_widgets[key]
            original_style = widget.styleSheet()
            widget.setStyleSheet("background-color: #FFEB3B; border-radius: 4px;")
            # Restaurar estilo original después de 500ms
            QTimer.singleShot(500, lambda: widget.setStyleSheet(original_style))
