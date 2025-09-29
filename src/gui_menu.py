from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import QDialog, QMenu

from src.gui_attack_dialog import AttackDialog


class Menu(QMenu):
    # Variable de clase para rastrear el país de origen para mover unidades
    pais_origen = None

    def __init__(self, pais, main_window, parent=None):
        # En Wayland, el menú necesita tener la ventana principal como padre
        # para evitar errores de "grabbing popup"
        super().__init__(parent or main_window)
        self.pais = pais
        self.main_window = main_window
        self.transmisor = main_window.transmisor

        # Configurar acciones del menú
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)

        # Acciones para agregar unidades
        self.action_agregar_infanteria = QAction("Agregar Infantería", self)
        self.action_agregar_misil = QAction("Agregar Misil", self)

        # Acciones para mover unidades (sistema antiguo)
        self.action_mover_1_unidad = QAction("Mover 1 unidad", self)
        self.action_mover_3_unidades = QAction("Mover 3 unidades", self)
        self.action_mover_5_unidades = QAction("Mover 5 unidades", self)
        self.action_cancelar_movimiento = QAction("Cancelar movimiento", self)

        # Acciones para el nuevo sistema de selección
        self.action_atacar = QAction("Atacar", self)
        self.action_mover_seleccion = QAction("Mover", self)
        self.action_cancelar_seleccion = QAction("Cancelar Selección", self)

        # Acción para canjear misil
        self.action_canjear_misil = QAction("Canjear Misil (6 unidades)", self)

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

    def actualizar_menu(self):
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
        misiles_habilitados = (
            hasattr(self.main_window, "misiles_habilitados")
            and self.main_window.misiles_habilitados
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
        selection_manager = getattr(self.main_window.scene, "selection_manager", None)
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

    def agregar_infanteria(self):
        if self.transmisor:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="infanteria")

    def agregar_misil(self):
        if self.transmisor:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="misil")

    def iniciar_movimiento(self):
        """Inicia el proceso de movimiento de unidades desde este país"""
        Menu.pais_origen = self.pais
        # Actualizar el menú en la ventana principal
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def completar_movimiento(self, cantidad):
        """Completa el movimiento de unidades desde el país de origen al país actual"""
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

    def cancelar_movimiento(self):
        """Cancela el proceso de movimiento de unidades"""
        Menu.pais_origen = None
        if hasattr(self.main_window, "actualizar_menus_contextuales"):
            self.main_window.actualizar_menus_contextuales()

    def atacar(self):
        """Ataca del país origen al país destino"""
        selection_manager = getattr(self.main_window.scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor:
                # Obtener información del país atacante para determinar
                # unidades disponibles
                max_unidades = self.main_window.get_max_attack_units(origen)

                if max_unidades < 1:
                    self.main_window.update_status_bar(
                        f"No hay suficientes unidades en {origen} para atacar", "orange"
                    )
                    return

                # Mostrar diálogo para seleccionar cantidad de unidades
                dialog = AttackDialog(origen, destino, max_unidades, self.main_window)
                if dialog.exec() == QDialog.Accepted:
                    cantidad_unidades = dialog.get_cantidad_unidades()
                    # Realizar ataque usando el método específico
                    self.transmisor.atacar(origen, destino, cantidad_unidades)
                    print(
                        f"Atacando de {origen} a {destino} con "
                        f"{cantidad_unidades} unidades"
                    )
                    # Mostrar mensaje en la barra de estado
                    self.main_window.update_status_bar(
                        f"Atacando de {origen} a {destino} con {cantidad_unidades} "
                        f"unidad{'es' if cantidad_unidades > 1 else ''}...",
                        "blue",
                    )

            # Limpiar selección después de la acción
            selection_manager.cancelar_seleccion()

    def mover(self):
        """Mueve unidades del país origen al país destino"""
        selection_manager = getattr(self.main_window.scene, "selection_manager", None)
        if selection_manager:
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and self.transmisor:
                # Realizar movimiento de 1 unidad
                self.transmisor.mover_unidad(origen=origen, destino=destino, cantidad=1)
                print(f"Moviendo 1 unidad de {origen} a {destino}")
                # Mostrar mensaje en la barra de estado
                self.main_window.status_bar.showMessage(
                    f"Moviendo 1 unidad de {origen} a {destino}",
                    3000,  # 3 segundos
                )

            # Limpiar selección después de la acción
            selection_manager.cancelar_seleccion()

    def cancelar_seleccion_menu(self):
        """Cancela la selección actual desde el menú contextual"""
        selection_manager = getattr(self.main_window.scene, "selection_manager", None)
        if selection_manager:
            selection_manager.cancelar_seleccion()

    def canjear_misil(self):
        """Canjea 6 unidades por 1 misil en el país actual"""
        if hasattr(self.main_window, "canjear_misil"):
            self.main_window.canjear_misil(self.pais)
