"""Gestión de la selección origen/destino de países sobre el mapa."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.gui_toolbar import ToolBar
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui_pais import Pais


class _MapSceneWithCountries(Protocol):
    """Escena mínima que expone el diccionario de widgets `Pais`."""

    paises: dict[str, Pais]


class CountrySelectionManager:
    """Maneja la selección de países origen y destino."""

    def __init__(self, main_window: Any, scene: _MapSceneWithCountries) -> None:
        """Inicializa el gestor de selección de países.

        Args:
            main_window: Ventana principal de la aplicación.
            scene: Escena gráfica donde se muestran los países.

        """
        self.main_window = main_window
        self.scene = scene
        self._pais_origen: str | None = None
        self._pais_destino: str | None = None
        self._pais_origen_widget: Pais | None = None
        self._pais_destino_widget: Pais | None = None

    def seleccionar_pais(self, nombre_pais: str) -> None:
        """Selecciona un país como origen o destino."""
        if self._pais_origen is None:
            self._pais_origen = nombre_pais
            self._pais_origen_widget = self.scene.paises.get(nombre_pais)
            if self._pais_origen_widget:
                self._pais_origen_widget.set_seleccion_visual("origen")
            self._actualizar_seleccion_label()
        elif self._pais_origen == nombre_pais:
            self.cancelar_seleccion()
        elif self._pais_destino is None:
            self._pais_destino = nombre_pais
            self._pais_destino_widget = self.scene.paises.get(nombre_pais)
            if self._pais_destino_widget:
                self._pais_destino_widget.set_seleccion_visual("destino")
            self._actualizar_seleccion_label()
        else:
            self.cancelar_seleccion()
            self.seleccionar_pais(nombre_pais)

    def cancelar_seleccion(self) -> None:
        """Cancela la selección actual de países."""
        if self._pais_origen_widget:
            self._pais_origen_widget.limpiar_seleccion_visual()
        if self._pais_destino_widget:
            self._pais_destino_widget.limpiar_seleccion_visual()

        self._pais_origen = None
        self._pais_destino = None
        self._pais_origen_widget = None
        self._pais_destino_widget = None
        self._actualizar_seleccion_label()

    def confirmar_seleccion(self) -> None:
        """Confirma la selección y ejecuta movimiento (acción por defecto)."""
        if (
            self._pais_origen
            and self._pais_destino
            and hasattr(self.main_window, "transmisor")
            and self.main_window.transmisor
        ):
            self.main_window.transmisor.mover_unidad(
                origen=self._pais_origen, destino=self._pais_destino, cantidad=1
            )
            self.main_window.status_bar.showMessage(
                _("Moviendo 1 unidad de {} a {}").format(
                    self._pais_origen, self._pais_destino
                ),
                3000,
            )
            self.cancelar_seleccion()

    def refresh_labels(self) -> None:
        """Re-aplica las traducciones del label de selección y notifica a la toolbar.

        Invocable desde `LanguageManager.on_language_changed` para refrescar el texto
        sin esperar a la próxima acción del usuario.
        """
        self._actualizar_seleccion_label()

    def _actualizar_seleccion_label(self) -> None:
        """Actualiza el label de selección en la barra de estado."""
        if hasattr(self.main_window, "seleccion_label"):
            if self._pais_origen is None:
                self.main_window.seleccion_label.setText(
                    _("Selección: Haz clic en un país para seleccionar origen")
                )
            elif self._pais_destino is None:
                self.main_window.seleccion_label.setText(
                    _("Origen: {} | Haz clic en otro país para destino").format(
                        self._pais_origen
                    )
                )
            else:
                self.main_window.seleccion_label.setText(
                    _(
                        "Origen: {origen} | Destino: {destino} | "
                        "Clic derecho: Atacar/Mover"
                    ).format(
                        origen=self._pais_origen,
                        destino=self._pais_destino,
                    )
                )

        self._actualizar_botones_toolbar()

    def get_pais_origen(self) -> str | None:
        """Retorna el país origen seleccionado.

        Returns:
            Nombre del país origen o None si no hay selección.

        """
        return self._pais_origen

    def get_pais_destino(self) -> str | None:
        """Retorna el país destino seleccionado.

        Returns:
            Nombre del país destino o None si no hay selección.

        """
        return self._pais_destino

    def _actualizar_botones_toolbar(self) -> None:
        """Actualiza el estado de los botones de atacar y mover en la toolbar."""
        hay_dos_paises = (
            self._pais_origen is not None and self._pais_destino is not None
        )

        if hasattr(self.main_window, "findChildren"):
            toolbars = self.main_window.findChildren(ToolBar)
            for toolbar in toolbars:
                if hasattr(toolbar, "actualizar_botones_seleccion"):
                    toolbar.actualizar_botones_seleccion(
                        hay_dos_paises_seleccionados=hay_dos_paises
                    )
