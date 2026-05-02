"""Estado de conexión y acciones de la toolbar ligadas al mapa y al transmisor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

from pyteg.i18n import translate as _


class ToolBarActionsMixin:
    """Habilitación de botones según conexión y selección de países en la escena."""

    main_window: Any
    button_conectar: QAction | None
    button_atacar: QAction | None
    button_mover: QAction | None

    def actualizar_botones_seleccion(
        self, *, hay_dos_paises_seleccionados: bool
    ) -> None:
        """Actualiza el estado de los botones de atacar y mover según la selección."""
        if self._esta_conectado():
            if self.button_atacar:
                self.button_atacar.setEnabled(hay_dos_paises_seleccionados)
            if self.button_mover:
                self.button_mover.setEnabled(hay_dos_paises_seleccionados)

    def actualizar_estado_conexion(self, *, conectado: bool) -> None:
        """Actualiza el estado de los botones según el estado de conexión."""
        if conectado:
            self._habilitar_botones_conectado()
        else:
            self._habilitar_solo_conectar()

    def _esta_conectado(self) -> bool:
        """Verifica si el cliente está conectado al servidor.

        Returns:
            True si está conectado, False en caso contrario.

        """
        if not hasattr(self.main_window, "transmisor"):
            return False
        if self.main_window.transmisor is None:
            return False
        if hasattr(self.main_window.transmisor, "esta_conectado"):
            result = self.main_window.transmisor.esta_conectado()
            return bool(result) if result is not None else False
        transmisor_type_name = type(self.main_window.transmisor).__name__
        return bool(not transmisor_type_name.endswith("NullTransmisor"))

    def _habilitar_solo_conectar(self) -> None:
        """Deshabilita todos los botones excepto el de conectar."""
        if self.button_conectar:
            self.button_conectar.setEnabled(True)
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
        if self.button_mover:
            self.button_mover.setEnabled(False)

    def _habilitar_botones_conectado(self) -> None:
        """Habilita los botones apropiados cuando está conectado."""
        if self.button_conectar:
            self.button_conectar.setEnabled(False)
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
        if self.button_mover:
            self.button_mover.setEnabled(False)

    def _atacar_paises_seleccionados(self) -> None:
        """Ejecuta ataque entre los países seleccionados."""
        if hasattr(self.main_window, "scene") and self.main_window.scene:
            selection_manager = self.main_window.scene.selection_manager
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and hasattr(self.main_window, "transmisor"):
                self.main_window.transmisor.mover_unidad(
                    origen=origen, destino=destino, cantidad=1
                )
                self.main_window.status_bar.showMessage(
                    _("Atacando desde {} hacia {}").format(origen, destino), 3000
                )
                selection_manager.cancelar_seleccion()

    def _mover_paises_seleccionados(self) -> None:
        """Ejecuta movimiento entre los países seleccionados."""
        if hasattr(self.main_window, "scene") and self.main_window.scene:
            selection_manager = self.main_window.scene.selection_manager
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and hasattr(self.main_window, "transmisor"):
                self.main_window.transmisor.mover_unidad(
                    origen=origen, destino=destino, cantidad=1
                )
                self.main_window.status_bar.showMessage(
                    _("Moviendo {} unidad(es) de {} a {}").format(1, origen, destino),
                    3000,
                )
                selection_manager.cancelar_seleccion()
