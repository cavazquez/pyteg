"""Acciones de refuerzo, ataque, movimiento con selección y canje de misil."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.gui.connection_utils import cliente_esta_conectado
from pyteg.gui.gameplay_state import avisar_fuera_de_turno, es_mi_turno

if TYPE_CHECKING:
    from pyteg.gui.mapa.menu.protocols import MenuHost


class MenuActionsMixin:
    """Colocar refuerzos, atacar, mover con `selection_manager`, canjear misil."""

    def colocar_unidad(self: MenuHost) -> None:
        """Coloca unidades en el país (el servidor elige el pool continental)."""
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if hasattr(self.main_window, "colocar_unidad_en_pais"):
            self.main_window.colocar_unidad_en_pais(self.pais, self.continente_mapa)
        elif cliente_esta_conectado(self.main_window) and self.transmisor is not None:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="infanteria")

    def atacar(self: MenuHost) -> None:
        """Ataca del país origen al país destino."""
        if hasattr(self.main_window, "atacar"):
            self.main_window.atacar()

    def mover(self: MenuHost) -> None:
        """Mueve unidades del país origen al país destino."""
        if hasattr(self.main_window, "mover"):
            self.main_window.mover()

    def cancelar_seleccion_menu(self: MenuHost) -> None:
        """Cancela la selección actual desde el menú contextual."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            selection_manager.cancelar_seleccion()

    def canjear_misil(self: MenuHost) -> None:
        """Canjea unidades por 1 misil en el país actual."""
        if hasattr(self.main_window, "canjear_misil"):
            self.main_window.canjear_misil(self.pais)

    def lanzar_misil(self: MenuHost) -> None:
        """Lanza un misil desde el país origen seleccionado hacia este país."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager and hasattr(self.main_window, "lanzar_misil"):
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()
            if origen and destino:
                self.main_window.lanzar_misil(origen, destino)
            selection_manager.cancelar_seleccion()
