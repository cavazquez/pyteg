"""Estado de conexión y acciones de la toolbar ligadas al mapa y al transmisor."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

    from pyteg.gui.managers.protocols import MainWindowProtocol

from pyteg.gui.gameplay_state import es_mi_turno


class ToolBarActionsMixin:
    """Habilitación de botones según conexión y selección de países en la escena."""

    main_window: MainWindowProtocol
    button_conectar: QAction | None
    button_atacar: QAction | None
    button_mover: QAction | None
    button_finalizar_turno: QAction | None

    def actualizar_botones_turno(self, *, es_mi_turno: bool) -> None:
        """Habilita acciones de juego solo durante el turno del jugador local."""
        if not self._esta_conectado():
            return
        if self.button_finalizar_turno:
            self.button_finalizar_turno.setEnabled(es_mi_turno)
        if not es_mi_turno:
            if self.button_atacar:
                self.button_atacar.setEnabled(False)
            if self.button_mover:
                self.button_mover.setEnabled(False)

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
        if self.button_finalizar_turno:
            self.button_finalizar_turno.setEnabled(es_mi_turno(self.main_window))

    def _mover_paises_seleccionados(self) -> None:
        """Ejecuta movimiento entre los países seleccionados."""
        if hasattr(self.main_window, "mover"):
            self.main_window.mover()
