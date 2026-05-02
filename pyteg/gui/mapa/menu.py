"""Módulo para el menú contextual de países."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QMenu, QWidget

from pyteg.config import MISSILE_UNIT_COST
from pyteg.gui_attack_dialog import AttackDialog
from pyteg.i18n import ngettext
from pyteg.i18n import translate as _
from pyteg.logger import get_logger

_LOG = get_logger("gui.menu")


class Menu(QMenu):
    """Menú contextual que se muestra al hacer clic derecho en un país."""

    # Variable de clase para rastrear el país de origen para mover unidades
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
        # En Wayland, el menú necesita tener la ventana principal como padre
        # para evitar errores de "grabbing popup"
        super().__init__(parent or main_window)
        self.pais = pais
        self.main_window = main_window
        self.transmisor = getattr(main_window, "transmisor", None)

        # i18n: este menú es efímero. `QCustomGraphicsScene.contextMenuEvent` lo
        # reconstruye en cada clic derecho, por lo que las etiquetas siempre se
        # crean con el idioma vigente y no se necesita un `refresh_labels()`
        # conectado a `LanguageManager` (a diferencia de la toolbar, que sí persiste).
        # Configurar acciones del menú
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)

        # Acciones para agregar unidades
        self.action_agregar_infanteria = QAction(_("Agregar Infantería"), self)
        self.action_agregar_misil = QAction(_("Agregar Misil"), self)

        # Acciones para mover unidades (sistema antiguo)
        self.action_mover_1_unidad = QAction(_("Mover 1 unidad"), self)
        self.action_mover_3_unidades = QAction(_("Mover 3 unidades"), self)
        self.action_mover_5_unidades = QAction(_("Mover 5 unidades"), self)
        self.action_cancelar_movimiento = QAction(_("Cancelar movimiento"), self)

        # Acciones para el nuevo sistema de selección
        self.action_atacar = QAction(_("Atacar"), self)
        self.action_mover_seleccion = QAction(_("Mover"), self)
        self.action_cancelar_seleccion = QAction(_("Cancelar selección"), self)

        # Acción para canjear misil
        self.action_canjear_misil = QAction(
            _("Canjear Misil ({} unidades)").format(MISSILE_UNIT_COST), self
        )

        # Conectar acciones a sus respectivos manejadores
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

        # Conectar acciones del nuevo sistema de selección
        self.action_atacar.triggered.connect(self.atacar)
        self.action_mover_seleccion.triggered.connect(self.mover)
        self.action_cancelar_seleccion.triggered.connect(self.cancelar_seleccion_menu)

        # Conectar acción de canjear misil
        self.action_canjear_misil.triggered.connect(self.canjear_misil)

        # Configurar el menú
        self.actualizar_menu()

    def actualizar_menu(self) -> None:
        """Actualiza las opciones del menú según el estado actual de selección."""
        # Limpiar el menú
        self.clear()

        # Agregar el título del país
        self.addAction(self.action_pais)
        self.addSeparator()

        # Mostrar opciones de agregar
        self.addAction(self.action_agregar_infanteria)
        self.addAction(self.action_agregar_misil)
        self.addSeparator()

        # Mostrar opción de canjear misil (solo si está habilitado)
        misiles_habilitados = bool(
            getattr(self.main_window, "misiles_habilitados", False)
        )
        if misiles_habilitados:
            self.addAction(self.action_canjear_misil)
            self.addSeparator()

        # Mostrar opciones de mover (sistema antiguo)
        if Menu.pais_origen is None:
            # Sin país de origen seleccionado
            pass
        elif Menu.pais_origen == self.pais:
            # Si este es el país de origen, mostrar opción para cancelar
            self.addAction(self.action_cancelar_movimiento)
        else:
            # Si hay un país de origen seleccionado,
            # mostrar opciones de mover 1, 3 o 5 unidades
            self.addAction(self.action_mover_1_unidad)
            self.addAction(self.action_mover_3_unidades)
            self.addAction(self.action_mover_5_unidades)
            self.addSeparator()
            self.addAction(self.action_cancelar_movimiento)

        # Agregar separador y opciones del nuevo sistema de selección
        self.addSeparator()

        # Opciones de selección basadas en el estado actual
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            pais_origen = selection_manager.get_pais_origen()
            pais_destino = selection_manager.get_pais_destino()
        else:
            pais_origen = None
            pais_destino = None

        if pais_origen is None:
            # No hay selección: no mostrar opciones de selección manual
            pass
        elif pais_origen == self.pais:
            # Este país es el origen: permitir cancelar
            self.addAction(self.action_cancelar_seleccion)
        elif pais_destino is None:
            # Hay origen pero no destino: solo mostrar cancelar
            self.addAction(self.action_cancelar_seleccion)
        else:
            # Hay origen y destino: permitir atacar, mover o cancelar
            if pais_destino == self.pais:
                self.addAction(self.action_atacar)
                self.addAction(self.action_mover_seleccion)
            self.addAction(self.action_cancelar_seleccion)

    def agregar_infanteria(self) -> None:
        """Agrega una unidad de infantería al país."""
        if self.transmisor is not None:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="infanteria")

    def agregar_misil(self) -> None:
        """Agrega un misil al país."""
        if self.transmisor is not None:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="misil")

    def iniciar_movimiento(self) -> None:
        """Inicia el proceso de movimiento de unidades desde este país."""
        Menu.pais_origen = self.pais
        # Actualizar el menú en la ventana principal
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def completar_movimiento(self, cantidad: int) -> None:
        """Completa el movimiento de unidades desde el país de origen al país actual."""
        if Menu.pais_origen is None or self.transmisor is None:
            return

        # Realizar el movimiento
        self.transmisor.mover_unidad(
            origen=Menu.pais_origen, destino=self.pais, cantidad=cantidad
        )

        # Reiniciar el país de origen
        Menu.pais_origen = None
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def cancelar_movimiento(self) -> None:
        """Cancela el proceso de movimiento de unidades."""
        Menu.pais_origen = None
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def atacar(self) -> None:
        """Ataca del país origen al país destino."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor:
                # Obtener información del país atacante para determinar
                # unidades disponibles
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

                # Mostrar diálogo para seleccionar cantidad de unidades
                dialog = AttackDialog(origen, destino, max_unidades, self.main_window)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    cantidad_unidades = dialog.get_cantidad_unidades()
                    # Realizar ataque usando el método específico
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

            # Limpiar selección después de la acción
            selection_manager.cancelar_seleccion()

    def mover(self) -> None:
        """Mueve unidades del país origen al país destino."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor is not None:
                # Realizar movimiento de 1 unidad
                self.transmisor.mover_unidad(origen=origen, destino=destino, cantidad=1)
                _LOG.debug("Moviendo 1 unidad de %s a %s", origen, destino)
                # Mostrar mensaje en la barra de estado
                status_bar = getattr(self.main_window, "status_bar", None)
                if status_bar is not None:
                    status_bar.showMessage(
                        _("Moviendo {} unidad(es) de {} a {}").format(
                            1, origen, destino
                        ),
                        3000,
                    )

            # Limpiar selección después de la acción
            selection_manager.cancelar_seleccion()

    def cancelar_seleccion_menu(self) -> None:
        """Cancela la selección actual desde el menú contextual."""
        scene = getattr(self.main_window, "scene", None)
        selection_manager = getattr(scene, "selection_manager", None)
        if selection_manager:
            selection_manager.cancelar_seleccion()

    def canjear_misil(self) -> None:
        """Canjea unidades por 1 misil en el país actual."""
        if hasattr(self.main_window, "canjear_misil"):
            self.main_window.canjear_misil(self.pais)
