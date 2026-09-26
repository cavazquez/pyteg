"""Menú contextual `QMenu` para un país del mapa."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from pyteg.gui.action_availability import (
    ActionAvailability,
    country_availability,
    selection_availability,
)
from pyteg.gui.mapa.menu.actions_mixin import MenuActionsMixin
from pyteg.gui.units_placement import tooltip_colocar_unidad
from pyteg.i18n import ngettext
from pyteg.i18n import translate as _

_PLACE_PRESETS = (1, 3, 5)


class Menu(MenuActionsMixin, QMenu):
    """Menú contextual de un país o del par origen/destino seleccionado."""

    def __init__(  # noqa: PLR0913 - Qt necesita padre y dos modos de menú.
        self,
        pais: str | None,
        continente_mapa: str | None,
        main_window: Any,
        parent: QWidget | None = None,
        *,
        solo_seleccion: bool = False,
        solo_pais: bool = False,
    ) -> None:
        """Inicializa el menú contextual para un país.

        Args:
            pais: País bajo el cursor, si el menú depende de un país concreto.
            continente_mapa: ID de continente del mapa (TOML), si aplica.
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional). En Wayland se usa main_window.
            solo_seleccion: Muestra las acciones del par origen/destino y,
                si se indica un país, sus acciones independientes debajo.
            solo_pais: Muestra sólo las acciones propias del país indicado.

        """
        super().__init__(parent or main_window)
        self.setToolTipsVisible(True)
        self.pais = pais
        self.continente_mapa = continente_mapa
        self.main_window = main_window
        self.transmisor = main_window.transmisor
        self.solo_seleccion = solo_seleccion
        self.solo_pais = solo_pais

        # i18n: este menú es efímero. `QCustomGraphicsScene.contextMenuEvent` lo
        # reconstruye en cada clic derecho, por lo que las etiquetas siempre se
        # crean con el idioma vigente y no se necesita un `refresh_labels()`
        # conectado a `LanguageManager` (a diferencia de la toolbar, que sí persiste).
        self.action_pais = QAction(pais or _("Países seleccionados"), self)
        self.action_pais.setEnabled(False)
        self.action_pais_clicado = QAction(
            _("Acciones en {}").format(pais) if pais is not None else "", self
        )
        self.action_pais_clicado.setEnabled(False)

        self.submenu_colocar = QMenu(_("Colocar unidad"), self)
        self.submenu_colocar.setToolTipsVisible(True)

        self.action_atacar = QAction(_("Atacar"), self)
        self.action_mover_seleccion = QAction(_("Mover"), self)
        self.action_cancelar_seleccion = QAction(_("Cancelar selección"), self)

        self.action_canjear_misil = QAction(_("Canjear Misil"), self)
        self.action_lanzar_misil = QAction(_("Lanzar misil"), self)

        self.action_atacar.triggered.connect(self.atacar)
        self.action_mover_seleccion.triggered.connect(self.mover)
        self.action_cancelar_seleccion.triggered.connect(self.cancelar_seleccion_menu)

        self.action_canjear_misil.triggered.connect(self.canjear_misil)
        self.action_lanzar_misil.triggered.connect(self.lanzar_misil)

        self.actualizar_menu()

    def actualizar_menu(self) -> None:
        """Actualiza las opciones del menú según el estado actual de selección."""
        self.clear()

        if self.solo_seleccion:
            self._actualizar_menu_seleccion()
            if self.pais is not None and self.continente_mapa is not None:
                self.addSeparator()
                self.addAction(self.action_pais_clicado)
                self._agregar_acciones_pais()
            return

        if self.pais is None or self.continente_mapa is None:
            return

        self.addAction(self.action_pais)
        self.addSeparator()

        self._agregar_acciones_pais()
        if self.solo_pais:
            return

        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            pais_origen = selection_manager.get_pais_origen()
            pais_destino = selection_manager.get_pais_destino()
        else:
            pais_origen = None
            pais_destino = None

        if pais_origen is not None:
            self.addSeparator()
            if pais_origen == self.pais or pais_destino is None:
                self.addAction(self.action_cancelar_seleccion)
            else:
                if pais_destino == self.pais:
                    self._agregar_acciones_par(pais_origen, pais_destino)
                self.addAction(self.action_cancelar_seleccion)

    def _agregar_acciones_pais(self) -> None:
        """Agrega las acciones que sólo afectan al país bajo el cursor."""
        if self.pais is None or self.continente_mapa is None:
            return

        available = country_availability(
            self.main_window, self.pais, self.continente_mapa
        )
        total = available.placeable_units
        last_units = getattr(self.main_window, "last_units", {})
        self.submenu_colocar.clear()
        place_help = available.place.explanation(
            tooltip_colocar_unidad(last_units, self.continente_mapa)
        )
        self.submenu_colocar.setToolTip(place_help)
        place_action = self.submenu_colocar.menuAction()
        place_action.setToolTip(place_help)
        place_action.setStatusTip(place_help)
        place_action.setWhatsThis(place_help)
        self.submenu_colocar.setEnabled(available.place.enabled)
        self._poblar_submenu_colocar(total)
        self.addMenu(self.submenu_colocar)

        misiles_habilitados = bool(
            getattr(self.main_window, "misiles_habilitados", False)
        )
        if misiles_habilitados:
            self.addSeparator()
            self.action_canjear_misil.setText(
                _("Canjear Misil ({} unidades)").format(available.missile_unit_cost)
            )
            self._configurar_accion(
                self.action_canjear_misil,
                available.exchange_missile,
                _("Canjear unidades por un misil en este país"),
            )
            self.addAction(self.action_canjear_misil)

    def _actualizar_menu_seleccion(self) -> None:
        """Muestra sólo acciones que usan el par origen/destino seleccionado."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager is None:
            return

        origen = selection_manager.get_pais_origen()
        destino = selection_manager.get_pais_destino()
        if origen is None or destino is None:
            return

        self.action_pais.setText(f"{origen} → {destino}")
        self.addAction(self.action_pais)
        self.addSeparator()

        self._agregar_acciones_par(origen, destino)

        self.addSeparator()
        self.addAction(self.action_cancelar_seleccion)

    def _agregar_acciones_par(self, origen: str, destino: str) -> None:
        """Usa la misma disponibilidad que la toolbar para el par."""
        available = selection_availability(self.main_window, origen, destino)
        self._configurar_accion(
            self.action_atacar, available.attack, _("Atacar país seleccionado")
        )
        self._configurar_accion(
            self.action_mover_seleccion,
            available.move,
            _("Mover unidades entre países"),
        )
        self.addAction(self.action_atacar)
        self.addAction(self.action_mover_seleccion)

        if getattr(
            self.main_window, "misiles_habilitados", False
        ) and self._puede_lanzar_misil(origen):
            self._configurar_accion(
                self.action_lanzar_misil,
                available.launch_missile,
                _("Lanzar misil al país seleccionado"),
            )
            self.addAction(self.action_lanzar_misil)

    @staticmethod
    def _configurar_accion(
        action: QAction, available: ActionAvailability, enabled_help: str
    ) -> None:
        """Muestra la disponibilidad y el motivo de bloqueo de una acción."""
        help_text = available.explanation(enabled_help)
        action.setEnabled(available.enabled)
        action.setToolTip(help_text)
        action.setStatusTip(help_text)
        action.setWhatsThis(help_text)

    def _poblar_submenu_colocar(self, total: int) -> None:
        """Añade cantidades 1/3/5 y atajo para el resto en un solo clic."""
        if total <= 0:
            return
        for cantidad in _PLACE_PRESETS:
            if cantidad <= total:
                etiqueta = _("Colocar {} {}").format(
                    cantidad,
                    ngettext("unidad", "unidades", cantidad),
                )
                action = self.submenu_colocar.addAction(etiqueta)
                action.triggered.connect(
                    lambda _checked=False, n=cantidad: self.colocar_unidades(n)
                )

        if total > max(_PLACE_PRESETS):
            action = self.submenu_colocar.addAction(
                _("Colocar todas ({})").format(total)
            )
            action.triggered.connect(
                lambda _checked=False, n=total: self.colocar_unidades(n)
            )
        elif total not in _PLACE_PRESETS:
            etiqueta = _("Colocar {} {}").format(
                total,
                ngettext("unidad", "unidades", total),
            )
            action = self.submenu_colocar.addAction(etiqueta)
            action.triggered.connect(
                lambda _checked=False, n=total: self.colocar_unidades(n)
            )

    def _puede_lanzar_misil(self, pais_origen: str | None) -> bool:
        if not pais_origen:
            return False
        scene = getattr(self.main_window, "scene", None)
        if scene is None or not hasattr(scene, "paises"):
            return False
        pais_widget = scene.paises.get(pais_origen)
        if pais_widget is None:
            return False
        return bool(pais_widget.get_cantidad_misiles() > 0)
