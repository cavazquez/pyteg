"""Menú contextual `QMenu` para un país del mapa."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from pyteg.config import MISSILE_UNIT_COST
from pyteg.gui.mapa.menu.actions_mixin import MenuActionsMixin
from pyteg.gui.units_placement import (
    tooltip_colocar_unidad,
    unidades_colocables_en_pais,
)
from pyteg.i18n import translate as _


class Menu(MenuActionsMixin, QMenu):
    """Menú contextual que se muestra al hacer clic derecho en un país."""

    def __init__(
        self,
        pais: str,
        continente_mapa: str,
        main_window: Any,
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa el menú contextual para un país.

        Args:
            pais: Nombre del país.
            continente_mapa: ID de continente del mapa (TOML).
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional). En Wayland se usa main_window.

        """
        super().__init__(parent or main_window)
        self.pais = pais
        self.continente_mapa = continente_mapa
        self.main_window = main_window
        self.transmisor = getattr(main_window, "transmisor", None)

        # i18n: este menú es efímero. `QCustomGraphicsScene.contextMenuEvent` lo
        # reconstruye en cada clic derecho, por lo que las etiquetas siempre se
        # crean con el idioma vigente y no se necesita un `refresh_labels()`
        # conectado a `LanguageManager` (a diferencia de la toolbar, que sí persiste).
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)

        self.action_colocar_unidad = QAction(_("Colocar unidad"), self)

        self.action_atacar = QAction(_("Atacar"), self)
        self.action_mover_seleccion = QAction(_("Mover"), self)
        self.action_cancelar_seleccion = QAction(_("Cancelar selección"), self)

        self.action_canjear_misil = QAction(
            _("Canjear Misil ({} unidades)").format(MISSILE_UNIT_COST), self
        )

        self.action_colocar_unidad.triggered.connect(self.colocar_unidad)

        self.action_atacar.triggered.connect(self.atacar)
        self.action_mover_seleccion.triggered.connect(self.mover)
        self.action_cancelar_seleccion.triggered.connect(self.cancelar_seleccion_menu)

        self.action_canjear_misil.triggered.connect(self.canjear_misil)

        self.actualizar_menu()

    def actualizar_menu(self) -> None:
        """Actualiza las opciones del menú según el estado actual de selección."""
        self.clear()

        self.addAction(self.action_pais)
        self.addSeparator()

        last_units = getattr(self.main_window, "last_units", {})
        total, _, _ = unidades_colocables_en_pais(last_units, self.continente_mapa)
        self.action_colocar_unidad.setEnabled(total > 0)
        self.action_colocar_unidad.setToolTip(
            tooltip_colocar_unidad(last_units, self.continente_mapa)
        )
        self.addAction(self.action_colocar_unidad)
        self.addSeparator()

        misiles_habilitados = bool(
            getattr(self.main_window, "misiles_habilitados", False)
        )
        if misiles_habilitados:
            self.addAction(self.action_canjear_misil)
            self.addSeparator()

        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            pais_origen = selection_manager.get_pais_origen()
            pais_destino = selection_manager.get_pais_destino()
        else:
            pais_origen = None
            pais_destino = None

        if pais_origen is None:
            pass
        elif pais_origen == self.pais or pais_destino is None:
            self.addAction(self.action_cancelar_seleccion)
        else:
            if pais_destino == self.pais:
                self.addAction(self.action_atacar)
                self.addAction(self.action_mover_seleccion)
            self.addAction(self.action_cancelar_seleccion)
