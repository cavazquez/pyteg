"""Módulo para gestión de ventanas en la interfaz gráfica.

Este módulo contiene la clase WindowManager que maneja toda la lógica
relacionada con la apertura y gestión de ventanas secundarias.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from pyteg.gui.dialogs.conectar import VentanaConectar
from pyteg.gui.windows.admin import VentanaAdmin
from pyteg.gui.windows.esperar_jugadores import VentanaEsperarJugadores
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol

_LOG = get_logger("gui.window_manager")


class WindowManager:
    """Gestiona las ventanas secundarias de la aplicación.

    Esta clase se encarga de crear, mostrar y gestionar el ciclo de vida
    de las ventanas secundarias como conexión, admin y espera de jugadores.
    """

    def __init__(self, main_window: MainWindowProtocol) -> None:
        """Inicializa el gestor de ventanas.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def abrir_ventana_conectar(self) -> None:
        """Abre la ventana de conexión al servidor."""
        # Cancelar selección al abrir ventana de conexión
        if self.main_window.scene and hasattr(
            self.main_window.scene, "selection_manager"
        ):
            self.main_window.scene.selection_manager.cancelar_seleccion()

        # Mantener referencia persistente para conexión al selector de idioma
        if (
            not hasattr(self.main_window, "ventana_conectar")
            or self.main_window.ventana_conectar is None
        ):
            self.main_window.ventana_conectar = VentanaConectar(self.main_window)

        self.main_window.ventana_conectar.show()

    def ventana_admin(self) -> None:
        """Abre la ventana de administración."""
        self.main_window.w = None
        self.main_window.w = VentanaAdmin(self.main_window)
        if self.main_window.w is not None:
            self.main_window.w.show()

    def ventana_esperar_jugadores(self) -> None:
        """Abre la ventana de espera de jugadores."""
        _LOG.debug("Iniciando ventana_esperar_jugadores")
        self.main_window.w = VentanaEsperarJugadores(self.main_window)

        # Conectar la señal de cierre para limpiar la referencia
        def limpiar_ventana() -> None:
            _LOG.debug("Limpiando referencia a la ventana de espera")
            if hasattr(self.main_window, "w") and self.main_window.w is not None:
                with contextlib.suppress(Exception):
                    # Desconectar todas las señales para evitar llamadas duplicadas
                    self.main_window.w.destroyed.disconnect()

                self.main_window.w = None

        if self.main_window.w is not None:
            self.main_window.w.destroyed.connect(limpiar_ventana)

        # Mostrar la ventana
        self.main_window.w.show()
        _LOG.debug("Ventana de espera mostrada")
