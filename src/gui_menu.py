from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QMenu,
)


class Menu(QMenu):
    def __init__(self, pais):
        super().__init__()
        self.action_pais = QAction(pais, self)
        self.action_pais.setEnabled(False)
        self.action1 = QAction("Opción 1", self)
        self.action2 = QAction("Opción 2", self)

        self.addAction(self.action_pais)
        self.addSeparator()
        self.addAction(self.action1)
        self.addAction(self.action2)
