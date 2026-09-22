"""Estado de conexión y acciones de la toolbar ligadas al mapa y al transmisor."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

    from pyteg.gui.managers.protocols import MainWindowProtocol

from pyteg.gui.gameplay_state import en_fase_reparto, es_mi_turno
from pyteg.i18n import translate as _


class ToolBarActionsMixin:
    """Habilitación de botones según conexión y selección de países en la escena."""

    main_window: MainWindowProtocol
    button_conectar: QAction | None
    button_atacar: QAction | None
    button_mover: QAction | None
    button_finalizar_turno: QAction | None

    def actualizar_botones_turno(
        self,
        *,
        es_mi_turno: bool,
        puede_finalizar_turno: bool | None = None,
    ) -> None:
        """Habilita acciones de juego solo durante el turno del jugador local."""
        if not self._esta_conectado():
            return
        if self.button_finalizar_turno:
            puede_cerrar = (
                es_mi_turno
                if puede_finalizar_turno is None
                else es_mi_turno and puede_finalizar_turno
            )
            self.button_finalizar_turno.setEnabled(puede_cerrar)
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

    def actualizar_motivos_acciones(
        self,
        *,
        hay_dos_paises_seleccionados: bool,
        puede_actuar: bool,
        es_mi_turno: bool,
    ) -> None:
        """Explica en cada acción por qué está deshabilitada.

        ``QAction`` no ofrece un estado visual adicional para indicar el
        motivo de una deshabilitación. El tooltip y el status tip cumplen ese
        papel sin agregar controles permanentes a la ventana.
        """
        conectado = self._esta_conectado()
        partida_finalizada = bool(
            getattr(self.main_window, "partida_finalizada", False)
        )
        motivo_comun = self._motivo_comun(
            conectado=conectado,
            partida_finalizada=partida_finalizada,
            es_mi_turno=es_mi_turno,
        )
        motivo_combate = self._motivo_combate(
            motivo_comun=motivo_comun,
            puede_actuar=puede_actuar,
            hay_dos_paises_seleccionados=hay_dos_paises_seleccionados,
        )
        self._actualizar_ayuda_accion(self.button_atacar, motivo_combate[0])
        self._actualizar_ayuda_accion(self.button_mover, motivo_combate[1])
        motivo_finalizar = self._motivo_finalizar(
            motivo_comun=motivo_comun,
            es_mi_turno=es_mi_turno,
        )
        self._actualizar_ayuda_accion(self.button_finalizar_turno, motivo_finalizar)

    def _motivo_comun(
        self,
        *,
        conectado: bool,
        partida_finalizada: bool,
        es_mi_turno: bool,
    ) -> str:
        """Obtiene el motivo compartido por las acciones de turno.

        Returns:
            Motivo común, o una cadena vacía si no hay bloqueo compartido.

        """
        if not conectado:
            return _("Conectate al servidor")
        if partida_finalizada:
            return _("La partida terminó")
        if not es_mi_turno:
            return _("Esperá tu turno")
        return ""

    def _motivo_combate(
        self,
        *,
        motivo_comun: str,
        puede_actuar: bool,
        hay_dos_paises_seleccionados: bool,
    ) -> tuple[str, str]:
        """Obtiene los motivos de atacar y mover, en ese orden.

        Returns:
            Motivos para las acciones de atacar y mover.

        """
        if motivo_comun:
            return motivo_comun, motivo_comun
        if en_fase_reparto(self.main_window):
            motivo = _("Colocá todas las unidades antes de atacar o mover")
            return motivo, motivo
        if not puede_actuar:
            motivo = _("La acción no está disponible ahora")
            return motivo, motivo
        if not hay_dos_paises_seleccionados:
            motivo = _("Seleccioná origen y destino")
            return motivo, motivo
        return _("Atacar país seleccionado"), _("Mover unidades entre países")

    def _motivo_finalizar(self, *, motivo_comun: str, es_mi_turno: bool) -> str:
        """Obtiene el motivo o la ayuda de finalizar el turno.

        Returns:
            Motivo de bloqueo o texto de ayuda de la acción.

        """
        if motivo_comun:
            return motivo_comun
        if not es_mi_turno:
            return _("Esperá tu turno")
        if en_fase_reparto(self.main_window):
            return _("Colocá todas las unidades antes de finalizar el turno")
        return _("Finalizar tu turno actual")

    @staticmethod
    def _actualizar_ayuda_accion(action: QAction | None, texto: str) -> None:
        """Sincroniza tooltip y mensaje de estado de una acción."""
        if action is None:
            return
        action.setToolTip(texto)
        action.setStatusTip(texto)

    def deshabilitar_acciones_juego(self) -> None:
        """Deshabilita las acciones que modifican la partida."""
        for button in (
            self.button_atacar,
            self.button_mover,
            self.button_finalizar_turno,
        ):
            if button:
                button.setEnabled(False)

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
