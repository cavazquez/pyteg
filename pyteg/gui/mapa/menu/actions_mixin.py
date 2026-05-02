"""Acciones de ataque, movimiento con selección y canje de misil."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog

from pyteg.gui_attack_dialog import AttackDialog
from pyteg.i18n import ngettext
from pyteg.i18n import translate as _
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.mapa.menu.protocols import MenuHost

_LOG = get_logger("gui.menu")


class MenuActionsMixin:
    """Atacar, mover con `selection_manager`, cancelar selección, canjear misil."""

    def atacar(self: MenuHost) -> None:
        """Ataca del país origen al país destino."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor:
                get_max_units = getattr(
                    self.main_window, "get_max_attack_units", lambda _: 0
                )
                max_unidades = get_max_units(origen)

                if max_unidades < 1:
                    self.main_window.update_status_bar(
                        _("No hay suficientes unidades en {} para atacar").format(
                            origen
                        ),
                        "orange",
                    )
                    return

                dialog = AttackDialog(origen, destino, max_unidades, self.main_window)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    cantidad_unidades = dialog.get_cantidad_unidades()
                    self.transmisor.atacar(origen, destino, cantidad_unidades)
                    _LOG.debug(
                        "Atacando de %s a %s con %s unidades",
                        origen,
                        destino,
                        cantidad_unidades,
                    )
                    unidad_txt = ngettext("unidad", "unidades", cantidad_unidades)
                    self.main_window.update_status_bar(
                        _("Atacando de {} a {} con {} {}…").format(
                            origen,
                            destino,
                            cantidad_unidades,
                            unidad_txt,
                        ),
                        "blue",
                    )

            selection_manager.cancelar_seleccion()

    def mover(self: MenuHost) -> None:
        """Mueve unidades del país origen al país destino (selección nueva)."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor is not None:
                self.transmisor.mover_unidad(origen=origen, destino=destino, cantidad=1)
                _LOG.debug("Moviendo 1 unidad de %s a %s", origen, destino)
                status_bar = getattr(self.main_window, "status_bar", None)
                if status_bar is not None:
                    status_bar.showMessage(
                        _("Moviendo {} unidad(es) de {} a {}").format(
                            1, origen, destino
                        ),
                        3000,
                    )

            selection_manager.cancelar_seleccion()

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
