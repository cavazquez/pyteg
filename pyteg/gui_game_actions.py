"""Módulo para gestión de acciones de juego en la interfaz gráfica.

Este módulo contiene la clase GameActionsManager que maneja toda la lógica
relacionada con las acciones del juego como atacar, finalizar turno y
cálculos de unidades disponibles para ataques.
"""

from __future__ import annotations

from typing import Any, cast

from PySide6.QtWidgets import QDialog

from pyteg.gui_attack_dialog import AttackDialog
from pyteg.logger import get_logger

_LOG = get_logger("gui.game_actions")


class GameActionsManager:
    """Gestiona las acciones del juego como atacar y finalizar turno.

    Esta clase se encarga de manejar la lógica de las acciones principales
    del juego, incluyendo validaciones, diálogos de confirmación y
    comunicación con el servidor.
    """

    def __init__(self, main_window: Any):
        """Inicializa el gestor de acciones de juego.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def atacar(self) -> None:
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        # Verificar que tenemos un selection_manager
        if not hasattr(self.main_window.scene, "selection_manager"):
            self.main_window.update_status_bar(
                "Error: No hay sistema de selección disponible", "red"
            )
            return

        selection_manager = self.main_window.scene.selection_manager
        origen = selection_manager.get_pais_origen()
        destino = selection_manager.get_pais_destino()

        if not origen:
            status_msg = "Selecciona un país de origen primero"
            self.main_window.update_status_bar(status_msg, "orange")
            return

        if not destino:
            self.main_window.update_status_bar(
                "Selecciona un país de destino después del origen", "orange"
            )
            return

        transmisor = self.main_window.transmisor
        has_transmisor = hasattr(self.main_window, "transmisor")
        has_atacar = hasattr(transmisor, "atacar") if has_transmisor else False
        if has_transmisor and has_atacar:
            # Obtener información del país atacante para determinar unidades disponibles
            max_unidades = self.get_max_attack_units(origen)

            if max_unidades < 1:
                self.main_window.update_status_bar(
                    f"No hay suficientes unidades en {origen} para atacar", "orange"
                )
                return

            # Mostrar diálogo para seleccionar cantidad de unidades
            dialog = AttackDialog(origen, destino, max_unidades, self.main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                cantidad_unidades = dialog.get_cantidad_unidades()
                self.main_window.transmisor.atacar(origen, destino, cantidad_unidades)
                self.main_window.update_status_bar(
                    f"Atacando de {origen} a {destino} con {cantidad_unidades} "
                    f"unidad{'es' if cantidad_unidades > 1 else ''}...",
                    "blue",
                )
                # Cancelar selección después de atacar
                selection_manager.cancelar_seleccion()
        else:
            error_msg = "Error: No hay conexión disponible"
            self.main_window.update_status_bar(error_msg, "red")

    def finalizar_turno(self) -> None:
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        # Aquí puedes agregar la lógica para finalizar el turno actual
        # Por ejemplo, notificar al servidor que el turno ha terminado
        transmisor = self.main_window.transmisor
        has_transmisor = hasattr(self.main_window, "transmisor")
        has_finalizar = (
            hasattr(transmisor, "finalizar_turno") if has_transmisor else False
        )
        if has_transmisor and has_finalizar:
            self.main_window.transmisor.finalizar_turno()
            # Cancelar selección después de finalizar turno
            if hasattr(self.main_window.scene, "selection_manager"):
                self.main_window.scene.selection_manager.cancelar_seleccion()
        else:
            _LOG.warning("No se pudo finalizar el turno: transmisor no disponible")

    def get_max_attack_units(self, pais: str) -> int:
        """Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)

        """
        # Buscar el país en la escena para obtener sus unidades
        scene = getattr(self.main_window, "scene", None)
        if scene is None or not hasattr(scene, "paises"):
            return 0

        paises = scene.paises
        if pais not in paises:
            return 0

        pais_widget = paises[pais]
        unidades_totales = cast("int", pais_widget.get_unidades())
        # Se necesita dejar al menos 1 unidad en el país
        unidades_disponibles = max(0, unidades_totales - 1)
        # Máximo 3 unidades para atacar
        return min(unidades_disponibles, 3)

    def canjear_misil(self, pais: str) -> None:
        """Canjea unidades por 1 misil en el país especificado.

        Args:
            pais: Nombre del país donde canjear el misil.

        """
        if self.main_window.transmisor:
            self.main_window.transmisor.canjear_misil(pais)
            self.main_window.status_bar.showMessage(
                f"Canjeando misil en {pais}...", 3000
            )

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen: País desde donde se lanza el misil.
            pais_destino: País objetivo del misil.

        """
        if self.main_window.transmisor:
            self.main_window.transmisor.lanzar_misil(pais_origen, pais_destino)
            self.main_window.status_bar.showMessage(
                f"Lanzando misil desde {pais_origen} hacia {pais_destino}...",
                3000,
            )
