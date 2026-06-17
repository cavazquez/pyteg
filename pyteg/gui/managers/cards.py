"""Módulo para gestión de tarjetas en la interfaz gráfica.

Este módulo contiene la clase CardManager que maneja toda la lógica
relacionada con las tarjetas del jugador.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.gui.tarjetas import TarjetasDialog

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from pyteg.gui.managers.protocols import MainWindowProtocol


class CardManager:
    """Gestiona las tarjetas del jugador.

    Esta clase se encarga de mostrar y gestionar el diálogo de tarjetas,
    incluyendo la solicitud de tarjetas al servidor.
    """

    def __init__(self, main_window: MainWindowProtocol) -> None:
        """Inicializa el gestor de tarjetas.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def mostrar_tarjetas(self) -> None:
        """Muestra la ventana de tarjetas del jugador."""
        # Solicitar tarjetas actualizadas al servidor
        if self.main_window.transmisor:
            self.main_window.transmisor.solicitar_tarjetas()

        dialog = TarjetasDialog(cast("QWidget", self.main_window))

        if self.main_window.tarjetas_jugador:
            dialog.actualizar_tarjetas(self.main_window.tarjetas_jugador)
        else:
            # Si no hay tarjetas, usar lista vacía para mostrar slots vacíos
            dialog.actualizar_tarjetas([])

        objetivo_id = self.main_window.config_manager.objetivo_secreto_id
        descripcion = self.main_window.config_manager.objetivo_secreto_descripcion
        if objetivo_id and descripcion:
            dialog.set_objetivo_secreto(objetivo_id, descripcion)

        dialog.exec()

    def refresh_open_tarjetas_dialogs(self, tarjetas: list[Any]) -> None:
        """Actualiza los diálogos de tarjetas abiertos con la lista provista.

        Args:
            tarjetas: Lista actualizada de tarjetas del jugador.

        """
        for widget in self.main_window.findChildren(TarjetasDialog):
            if widget.isVisible():
                widget.actualizar_tarjetas(tarjetas)
