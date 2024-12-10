from PySide6.QtWidgets import (
    QRadioButton,
)


class GuiRadioButtonColor(QRadioButton):
    def __init__(self, label, parent, main_window, color):
        super().__init__(label, parent)
        self._main_window = main_window
        self._color = color
        self.toggled.connect(self.seleccionar_boton)

    def seleccionar_boton(self, checked):
        if checked:
            self._main_window.transmisor.seleccionar_color(self._color)
