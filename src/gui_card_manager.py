"""Módulo para gestión de tarjetas en la interfaz gráfica.

Este módulo contiene la clase CardManager que maneja toda la lógica
relacionada con las tarjetas del jugador.
"""

from __future__ import annotations

from typing import Any

from src.gui_tarjetas_dialog import TarjetasDialog


class CardManager:
    """Gestiona las tarjetas del jugador.

    Esta clase se encarga de mostrar y gestionar el diálogo de tarjetas,
    incluyendo la solicitud de tarjetas al servidor.
    """

    def __init__(self, main_window: Any) -> None:
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

        dialog = TarjetasDialog(self.main_window)

        # Si tenemos tarjetas del servidor, usarlas inmediatamente
        if (
            hasattr(self.main_window, "tarjetas_jugador")
            and self.main_window.tarjetas_jugador
        ):
            dialog.actualizar_tarjetas(self.main_window.tarjetas_jugador)
        else:
            # Si no hay tarjetas, usar lista vacía para mostrar slots vacíos
            dialog.actualizar_tarjetas([])

        # Si tenemos un objetivo secreto, mostrarlo en el diálogo
        if hasattr(self.main_window, "config_manager"):
            objetivo_id = self.main_window.config_manager.objetivo_secreto_id
            descripcion = self.main_window.config_manager.objetivo_secreto_descripcion
            if objetivo_id and descripcion:
                dialog.set_objetivo_secreto(objetivo_id, descripcion)

        dialog.exec()
