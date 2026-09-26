"""Estado de conexión y acciones de la toolbar ligadas al mapa y al transmisor."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QWidget

    from pyteg.gui.action_availability import SelectionAvailability
    from pyteg.gui.managers.protocols import MainWindowProtocol

from pyteg.gui.gameplay_state import en_fase_reparto, es_mi_turno
from pyteg.gui.toolbar.icons import cargar_icono_toolbar
from pyteg.i18n import translate as _


class ToolBarActionsMixin:
    """Habilitación de botones según conexión y selección de países en la escena."""

    main_window: MainWindowProtocol
    button_conectar: QAction | None
    button_tarjetas: QAction | None
    button_atacar: QAction | None
    button_mover: QAction | None
    button_finalizar_turno: QAction | None

    def aplicar_disponibilidad(self, available: SelectionAvailability) -> None:
        """Aplica la misma decisión que usa el menú contextual."""
        for action, state, help_text in (
            (self.button_atacar, available.attack, _("Atacar país seleccionado")),
            (self.button_mover, available.move, _("Mover unidades entre países")),
            (
                self.button_finalizar_turno,
                available.finish_turn,
                _("Finalizar tu turno actual"),
            ),
            (self.button_tarjetas, available.cards, _("Ver mis tarjetas")),
        ):
            if action is None:
                continue
            action.setEnabled(state.enabled)
            self._actualizar_ayuda_accion(action, state.explanation(help_text))

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
        if getattr(self.main_window, "estado_actual", "JUGANDO") in {
            "INICIAL",
            "EsperarJugadores",
            "Conectado",
        }:
            return _("Esperá a que comience la partida")
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
        action.setWhatsThis(texto)

    def deshabilitar_acciones_juego(self) -> None:
        """Deshabilita las acciones que modifican la partida."""
        for button in (
            self.button_atacar,
            self.button_mover,
            self.button_finalizar_turno,
        ):
            if button:
                button.setEnabled(False)
                self._actualizar_ayuda_accion(button, _("La partida terminó"))

    def actualizar_estado_conexion(self, *, conectado: bool) -> None:
        """Actualiza el estado de los botones según el estado de conexión."""
        if conectado:
            self._habilitar_botones_conectado()
        else:
            self._habilitar_solo_conectar()
        refresh_actions = getattr(self.main_window, "refresh_gameplay_actions", None)
        if callable(refresh_actions):
            refresh_actions()

    def _accion_conexion(self) -> None:
        """Abre la conexión o cierra la sesión activa desde el mismo botón."""
        if not self._esta_conectado():
            self.main_window.abrir_ventana_conectar()
            return

        en_partida = getattr(
            self.main_window, "estado_actual", None
        ) == "JUGANDO" and not getattr(self.main_window, "partida_finalizada", False)
        if en_partida:
            respuesta = QMessageBox.question(
                cast("QWidget", self.main_window),
                _("Desconectar"),
                _("¿Querés desconectarte de la partida actual?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return

        conexion = self.main_window.conexion
        if conexion is not None:
            conexion.desconectar()

    def _actualizar_accion_conexion(self, *, conectado: bool) -> None:
        """Cambia etiqueta, ayuda e ícono al conectar o desconectar."""
        if self.button_conectar is None:
            return
        accion = self.button_conectar
        accion.setEnabled(True)
        if conectado:
            accion.setText(_("Desconectar"))
            accion.setIcon(cargar_icono_toolbar("icons/disconnect.svg", "desconectar"))
            accion.setToolTip(_("Desconectar del servidor"))
            accion.setStatusTip(_("Salir de la conexión actual"))
        else:
            accion.setText(_("Conectar"))
            accion.setIcon(cargar_icono_toolbar("icons/conectar.png", "conectar"))
            accion.setToolTip(_("Conectar al servidor"))
            accion.setStatusTip(_("Abrir ventana de conexión"))

    def _actualizar_ayuda_tarjetas(self) -> None:
        """Explica por qué Tarjetas no está disponible sin conexión."""
        button_tarjetas = getattr(self, "button_tarjetas", None)
        if button_tarjetas is None:
            return
        if not self._esta_conectado():
            self._actualizar_ayuda_accion(button_tarjetas, _("Conectate al servidor"))
            return
        button_tarjetas.setToolTip(_("Ver mis tarjetas"))
        button_tarjetas.setStatusTip(_("Mostrar tarjetas asignadas al jugador"))
        button_tarjetas.setWhatsThis(_("Ver mis tarjetas"))

    def _esta_conectado(self) -> bool:
        """Verifica si el cliente está conectado al servidor.

        Returns:
            True si está conectado, False en caso contrario.

        """
        return bool(self.main_window.transmisor.esta_conectado())

    def _habilitar_solo_conectar(self) -> None:
        """Deshabilita todos los botones excepto el de conectar."""
        self._actualizar_accion_conexion(conectado=False)
        button_tarjetas = getattr(self, "button_tarjetas", None)
        if button_tarjetas:
            button_tarjetas.setEnabled(False)
            self._actualizar_ayuda_tarjetas()
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
            self._actualizar_ayuda_accion(
                self.button_atacar, _("Conectate al servidor")
            )
        if self.button_mover:
            self.button_mover.setEnabled(False)
            self._actualizar_ayuda_accion(self.button_mover, _("Conectate al servidor"))
        if self.button_finalizar_turno:
            self.button_finalizar_turno.setEnabled(False)
            self._actualizar_ayuda_accion(
                self.button_finalizar_turno, _("Conectate al servidor")
            )

    def _habilitar_botones_conectado(self) -> None:
        """Habilita los botones apropiados cuando está conectado."""
        self._actualizar_accion_conexion(conectado=True)
        button_tarjetas = getattr(self, "button_tarjetas", None)
        if button_tarjetas:
            button_tarjetas.setEnabled(True)
            self._actualizar_ayuda_tarjetas()
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
        if self.button_mover:
            self.button_mover.setEnabled(False)
        if self.button_finalizar_turno:
            self.button_finalizar_turno.setEnabled(es_mi_turno(self.main_window))
        self.actualizar_motivos_acciones(
            hay_dos_paises_seleccionados=False,
            puede_actuar=False,
            es_mi_turno=es_mi_turno(self.main_window),
        )

    def _mover_paises_seleccionados(self) -> None:
        """Ejecuta movimiento entre los países seleccionados."""
        if hasattr(self.main_window, "mover"):
            self.main_window.mover()
