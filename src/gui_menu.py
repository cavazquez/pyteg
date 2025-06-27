from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import QMenu


class Menu(QMenu):
    # Variable de clase para rastrear el país de origen para mover unidades
    pais_origen = None

    def __init__(self, pais, main_window, parent=None):
        super().__init__(parent)
        self.pais = pais
        self.main_window = main_window
        self.transmisor = main_window.transmisor

        # Configurar acciones del menú
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)

        # Acciones para agregar unidades
        self.action_agregar_infanteria = QAction("Agregar Infantería", self)
        self.action_agregar_misil = QAction("Agregar Misil", self)

        # Acciones para mover unidades
        self.action_mover_unidades = QAction("Mover unidades desde aquí", self)
        self.action_mover_1_unidad = QAction("Mover 1 unidad", self)
        self.action_mover_3_unidades = QAction("Mover 3 unidades", self)
        self.action_mover_5_unidades = QAction("Mover 5 unidades", self)
        self.action_cancelar_movimiento = QAction("Cancelar movimiento", self)

        # Conectar acciones a sus respectivos manejadores
        self.action_agregar_infanteria.triggered.connect(self.agregar_infanteria)
        self.action_agregar_misil.triggered.connect(self.agregar_misil)
        self.action_mover_unidades.triggered.connect(self.iniciar_movimiento)
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

        # Mostrar opciones de mover
        if Menu.pais_origen is None:
            # Si no hay país de origen seleccionado, mostrar
            # opción para iniciar movimiento
            self.addAction(self.action_mover_unidades)
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
