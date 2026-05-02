"""Movimiento clásico por menú y refuerzos en país (+infantería / +misil)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteg.gui.mapa.menu.protocols import MenuHost


class MenuOldMovementMixin:
    """Agregar unidades y movimiento antiguo (`pais_origen` de clase)."""

    def agregar_infanteria(self: MenuHost) -> None:
        """Agrega una unidad de infantería al país."""
        if self.transmisor is not None:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="infanteria")

    def agregar_misil(self: MenuHost) -> None:
        """Agrega un misil al país."""
        if self.transmisor is not None:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="misil")

    def iniciar_movimiento(self: MenuHost) -> None:
        """Inicia el proceso de movimiento de unidades desde este país."""
        cls: Any = type(self)
        cls.pais_origen = self.pais
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def completar_movimiento(self: MenuHost, cantidad: int) -> None:
        """Completa el movimiento desde el país de origen al país actual."""
        cls: Any = type(self)
        if cls.pais_origen is None or self.transmisor is None:
            return

        self.transmisor.mover_unidad(
            origen=cls.pais_origen, destino=self.pais, cantidad=cantidad
        )

        cls.pais_origen = None
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def cancelar_movimiento(self: MenuHost) -> None:
        """Cancela el proceso de movimiento de unidades (sistema antiguo)."""
        cls: Any = type(self)
        cls.pais_origen = None
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()
