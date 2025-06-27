from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QMenu,
)


class Menu(QMenu):
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

        # Conectar acciones a sus respectivos manejadores
        self.action_agregar_infanteria.triggered.connect(self.agregar_infanteria)
        self.action_agregar_misil.triggered.connect(self.agregar_misil)

        # Agregar acciones al menú
        self.addAction(self.action_pais)
        self.addSeparator()
        self.addAction(self.action_agregar_infanteria)
        self.addAction(self.action_agregar_misil)

    def agregar_infanteria(self):
        if self.transmisor:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="infanteria")

    def agregar_misil(self):
        if self.transmisor:
            self.transmisor.agregar_unidad(pais=self.pais, tipo_unidad="misil")
