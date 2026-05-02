"""Menú contextual `QMenu` para un país del mapa."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from pyteg.config import MISSILE_UNIT_COST
from pyteg.gui.mapa.menu.actions_mixin import MenuActionsMixin
from pyteg.gui.mapa.menu.old_movement_mixin import MenuOldMovementMixin
from pyteg.i18n import translate as _


class Menu(MenuActionsMixin, MenuOldMovementMixin, QMenu):
    """Menú contextual que se muestra al hacer clic derecho en un país."""

    pais_origen: str | None = None

    def __init__(
        self,
        pais: str,
        main_window: Any,
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa el menú contextual para un país.

        Args:
            pais: Nombre del país.
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional). En Wayland se usa main_window.

        """
        super().__init__(parent or main_window)
        self.pais = pais
        self.main_window = main_window
        self.transmisor = getattr(main_window, "transmisor", None)

        # i18n: este menú es efímero. `QCustomGraphicsScene.contextMenuEvent` lo
        # reconstruye en cada clic derecho, por lo que las etiquetas siempre se
        # crean con el idioma vigente y no se necesita un `refresh_labels()`
        # conectado a `LanguageManager` (a diferencia de la toolbar, que sí persiste).
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)

        self.action_agregar_infanteria = QAction(_("Agregar Infantería"), self)
        self.action_agregar_misil = QAction(_("Agregar Misil"), self)

        self.action_mover_1_unidad = QAction(_("Mover 1 unidad"), self)
        self.action_mover_3_unidades = QAction(_("Mover 3 unidades"), self)
        self.action_mover_5_unidades = QAction(_("Mover 5 unidades"), self)
        self.action_cancelar_movimiento = QAction(_("Cancelar movimiento"), self)

        self.action_atacar = QAction(_("Atacar"), self)
        self.action_mover_seleccion = QAction(_("Mover"), self)
        self.action_cancelar_seleccion = QAction(_("Cancelar selección"), self)

        self.action_canjear_misil = QAction(
            _("Canjear Misil ({} unidades)").format(MISSILE_UNIT_COST), self
        )

        self.action_agregar_infanteria.triggered.connect(self.agregar_infanteria)
        self.action_agregar_misil.triggered.connect(self.agregar_misil)
        self.action_mover_1_unidad.triggered.connect(
            lambda: self.completar_movimiento(1)
        )
        self.action_mover_3_unidades.triggered.connect(
            lambda: self.completar_movimiento(3)
        )
        self.action_mover_5_unidades.triggered.connect(
            lambda: self.completar_movimiento(5)
        )
        self.action_cancelar_movimiento.triggered.connect(self.cancelar_movimiento)

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

        self.addAction(self.action_agregar_infanteria)
        self.addAction(self.action_agregar_misil)
        self.addSeparator()

        misiles_habilitados = bool(
            getattr(self.main_window, "misiles_habilitados", False)
        )
        if misiles_habilitados:
            self.addAction(self.action_canjear_misil)
            self.addSeparator()

        cls = type(self)
        if cls.pais_origen is None:
            pass
        elif cls.pais_origen == self.pais:
            self.addAction(self.action_cancelar_movimiento)
        else:
            self.addAction(self.action_mover_1_unidad)
            self.addAction(self.action_mover_3_unidades)
            self.addAction(self.action_mover_5_unidades)
            self.addSeparator()
            self.addAction(self.action_cancelar_movimiento)

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
