"""Módulo para gestión de acciones de juego en la interfaz gráfica.

Este módulo contiene la clase GameActionsManager que maneja toda la lógica
relacionada con las acciones del juego como atacar, finalizar turno y
cálculos de unidades disponibles para ataques.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from pyteg.gui.connection_utils import cliente_esta_conectado
from pyteg.gui.dialogs.attack import AttackDialog
from pyteg.gui.dialogs.move import MoveDialog
from pyteg.gui.dialogs.place import PlaceUnitsDialog
from pyteg.gui.gameplay_state import (
    avisar_fase_reparto,
    avisar_fuera_de_turno,
    es_mi_turno,
    puede_atacar_o_mover,
)
from pyteg.gui.mapa.map_rules import es_mi_pais, es_pais_enemigo, son_adyacentes
from pyteg.gui.units_placement import unidades_colocables_en_pais
from pyteg.i18n import _, ngettext
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol

_LOG = get_logger("gui.game_actions")


class GameActionsManager:
    """Gestiona las acciones del juego como atacar y finalizar turno.

    Esta clase se encarga de manejar la lógica de las acciones principales
    del juego, incluyendo validaciones, diálogos de confirmación y
    comunicación con el servidor.
    """

    def __init__(self, main_window: MainWindowProtocol):
        """Inicializa el gestor de acciones de juego.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

    def atacar(self) -> None:  # noqa: PLR0911, PLR0912
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not puede_atacar_o_mover(self.main_window):
            avisar_fase_reparto(self.main_window)
            return
        scene = self.main_window.scene
        if scene is None or not hasattr(scene, "selection_manager"):
            self.main_window.update_status_bar(
                _("Error: No hay sistema de selección disponible"), "red"
            )
            return

        selection_manager = scene.selection_manager
        origen = selection_manager.get_pais_origen()
        destino = selection_manager.get_pais_destino()

        if not origen:
            status_msg = _("Selecciona un país de origen primero")
            self.main_window.update_status_bar(status_msg, "orange")
            return

        if not destino:
            self.main_window.update_status_bar(
                _("Selecciona un país de destino después del origen"), "orange"
            )
            return

        theme = getattr(self.main_window, "map_theme", "classic")
        if not es_mi_pais(self.main_window, origen):
            self.main_window.update_status_bar(
                _("{} no es tu país").format(origen), "orange"
            )
            return
        if not es_pais_enemigo(self.main_window, destino):
            self.main_window.update_status_bar(
                _("No puedes atacar tu propio país"), "orange"
            )
            return
        if not son_adyacentes(theme, origen, destino):
            self.main_window.update_status_bar(
                _("{} no es adyacente a {}").format(destino, origen), "orange"
            )
            return

        transmisor = self.main_window.transmisor
        if not cliente_esta_conectado(self.main_window):
            self.main_window.update_status_bar(
                _("Error: No hay conexión disponible"), "red"
            )
            return

        if hasattr(transmisor, "atacar"):
            # Obtener información del país atacante para determinar unidades disponibles
            max_unidades = self.get_max_attack_units(origen)

            if max_unidades < 1:
                self.main_window.update_status_bar(
                    _("No hay suficientes unidades en {} para atacar").format(origen),
                    "orange",
                )
                return

            # Mostrar diálogo para seleccionar cantidad de unidades
            dialog = AttackDialog(
                origen, destino, max_unidades, cast("QWidget", self.main_window)
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                cantidad_unidades = dialog.get_cantidad_unidades()
                self.main_window.transmisor.atacar(origen, destino, cantidad_unidades)
                self.main_window.update_status_bar(
                    _("Atacando de {} a {} con {} {}…").format(
                        origen,
                        destino,
                        cantidad_unidades,
                        ngettext("unidad", "unidades", cantidad_unidades),
                    ),
                    "blue",
                )
                # Cancelar selección después de atacar
                selection_manager.cancelar_seleccion()
        else:
            error_msg = _("Error: No hay conexión disponible")
            self.main_window.update_status_bar(error_msg, "red")

    def get_max_move_units(self, pais: str) -> int:
        """Unidades movibles desde un país (debe quedar al menos 1 en origen).

        Args:
            pais: Nombre del país de origen.

        Returns:
            Cantidad máxima de unidades que se pueden mover.

        """
        scene = self.main_window.scene
        if scene is None or not hasattr(scene, "paises"):
            return 0

        paises = scene.paises
        if pais not in paises:
            return 0

        unidades_totales = paises[pais].get_unidades()
        return max(0, unidades_totales - 1)

    def mover(self, origen: str | None = None, destino: str | None = None) -> None:  # noqa: PLR0911, PLR0912
        """Mueve unidades entre países seleccionados (toolbar o menú contextual)."""
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not puede_atacar_o_mover(self.main_window):
            avisar_fase_reparto(self.main_window)
            return
        scene = self.main_window.scene
        if scene is None or not hasattr(scene, "selection_manager"):
            self.main_window.update_status_bar(
                _("Error: No hay sistema de selección disponible"), "red"
            )
            return

        selection_manager = scene.selection_manager
        if origen is None:
            origen = selection_manager.get_pais_origen()
        if destino is None:
            destino = selection_manager.get_pais_destino()

        if not origen:
            self.main_window.update_status_bar(
                _("Selecciona un país de origen primero"), "orange"
            )
            return

        if not destino:
            self.main_window.update_status_bar(
                _("Selecciona un país de destino después del origen"), "orange"
            )
            return

        theme = getattr(self.main_window, "map_theme", "classic")
        if not es_mi_pais(self.main_window, origen):
            self.main_window.update_status_bar(
                _("{} no es tu país").format(origen), "orange"
            )
            return
        if not es_mi_pais(self.main_window, destino):
            self.main_window.update_status_bar(
                _("Solo puedes mover a países propios"), "orange"
            )
            return
        if not son_adyacentes(theme, origen, destino):
            self.main_window.update_status_bar(
                _("{} no es adyacente a {}").format(destino, origen), "orange"
            )
            return

        if not cliente_esta_conectado(self.main_window):
            self.main_window.update_status_bar(
                _("Error: No hay conexión disponible"), "red"
            )
            return

        max_unidades = self.get_max_move_units(origen)
        if max_unidades < 1:
            self.main_window.update_status_bar(
                _("No hay suficientes unidades en {} para mover").format(origen),
                "orange",
            )
            return

        dialog = MoveDialog(
            origen, destino, max_unidades, cast("QWidget", self.main_window)
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        cantidad = dialog.get_cantidad_unidades()
        self.main_window.transmisor.mover_unidad(
            origen=origen, destino=destino, cantidad=cantidad
        )
        self.main_window.update_status_bar(
            _("Moviendo {} {} de {} a {}…").format(
                cantidad,
                ngettext("unidad", "unidades", cantidad),
                origen,
                destino,
            ),
            "blue",
        )
        selection_manager.cancelar_seleccion()

    def finalizar_turno(self) -> None:
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not cliente_esta_conectado(self.main_window):
            _LOG.warning("No se pudo finalizar el turno: sin conexión")
            return

        self.main_window.transmisor.finalizar_turno()
        scene = self.main_window.scene
        if scene is not None and hasattr(scene, "selection_manager"):
            scene.selection_manager.cancelar_seleccion()

    def get_max_attack_units(self, pais: str) -> int:
        """Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)

        """
        scene = self.main_window.scene
        if scene is None or not hasattr(scene, "paises"):
            return 0

        paises = scene.paises
        if pais not in paises:
            return 0

        pais_widget = paises[pais]
        unidades_totales = pais_widget.get_unidades()
        # Se necesita dejar al menos 1 unidad en el país
        unidades_disponibles = max(0, unidades_totales - 1)
        # Máximo 3 unidades para atacar
        return min(unidades_disponibles, 3)

    def canjear_misil(self, pais: str) -> None:
        """Canjea unidades por 1 misil en el país especificado.

        Args:
            pais: Nombre del país donde canjear el misil.

        """
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not cliente_esta_conectado(self.main_window):
            return

        self.main_window.transmisor.canjear_misil(pais)
        self.main_window.status_bar.showMessage(f"Canjeando misil en {pais}...", 3000)

    def colocar_unidad_en_pais(self, pais: str, continente_mapa: str) -> None:
        """Abre diálogo y coloca unidades en un país."""
        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not cliente_esta_conectado(self.main_window):
            self.main_window.update_status_bar(
                _("Error: No hay conexión disponible"), "red"
            )
            return

        last_units = getattr(self.main_window, "last_units", {})
        total, _cont_pool, _gen_pool = unidades_colocables_en_pais(
            last_units, continente_mapa
        )
        if total < 1:
            self.main_window.update_status_bar(
                _("Sin unidades disponibles para este país"), "orange"
            )
            return

        dialog = PlaceUnitsDialog(pais, total, cast("QWidget", self.main_window))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        cantidad = dialog.get_cantidad()
        self.main_window.ultimo_pais_colocado = pais
        self.main_window.ultimo_continente_colocado = continente_mapa
        self.main_window.unidades_antes_colocar = dict(last_units)

        self.main_window.transmisor.agregar_unidad(
            pais=pais, tipo_unidad="infanteria", cantidad=cantidad
        )

        self.main_window.update_status_bar(
            _("Colocando {} {} en {}…").format(
                cantidad,
                ngettext("unidad", "unidades", cantidad),
                pais,
            ),
            "blue",
        )

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen: País desde donde se lanza el misil.
            pais_destino: País objetivo del misil.

        """
        if not cliente_esta_conectado(self.main_window):
            return

        if not es_mi_turno(self.main_window):
            avisar_fuera_de_turno(self.main_window)
            return
        if not puede_atacar_o_mover(self.main_window):
            avisar_fase_reparto(self.main_window)
            return

        if not es_mi_pais(self.main_window, pais_origen):
            self.main_window.update_status_bar(
                _("{} no es tu país").format(pais_origen), "orange"
            )
            return
        if not es_pais_enemigo(self.main_window, pais_destino):
            self.main_window.update_status_bar(
                _("No puedes lanzar misiles a tus propios países"), "orange"
            )
            return

        reply = QMessageBox.question(
            cast("QWidget", self.main_window),
            _("Lanzar misil"),
            _("¿Lanzar misil de {} a {}?").format(pais_origen, pais_destino),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.main_window.transmisor.lanzar_misil(pais_origen, pais_destino)
        self.main_window.update_status_bar(
            _("Lanzando misil de {} a {}…").format(pais_origen, pais_destino),
            "blue",
        )
