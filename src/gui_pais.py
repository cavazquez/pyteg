import pathlib

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGraphicsPixmapItem,
)

from src.exception import ImagenNoEncontradaError
from src.gui_circulo import Circulo


class Pais(QGraphicsPixmapItem):
    def __init__(self, path, pais, pos):
        # Validar que el archivo de imagen existe
        if not pathlib.Path(path).exists():
            raise ImagenNoEncontradaError(
                path, f"imagen del país {pais[0]} en continente {pais[1]}"
            )

        # Intentar cargar la imagen
        pixmap = QPixmap(path)
        if pixmap.isNull():
            raise ImagenNoEncontradaError(
                path,
                f"la imagen del país {pais[0]} no se pudo cargar (formato inválido)",
            )

        super().__init__(pixmap)
        self._nombre, self._continente = pais
        self._x, self._y, self._army_x, self._army_y = pos
        self.setPos(self._x, self._y)
        self._circle = None
        self._center_text = None
        self._main_window = None

        self.cargar_circulo()

    def cargar_circulo(self):
        pos_x_abs = self._army_x
        pos_y_abs = self._army_y
        # (x, y)
        self._circle = Circulo(pos_x_abs, pos_y_abs)
        self._circle.setParentItem(self)

    def nombre(self):
        return self._nombre

    def set_color(self, color):
        if color:
            self._circle.set_color(color)

    def set_unidades(self, cant):
        self._circle.set_unidades(cant)

    def set_main_window(self, main_window):
        """Establece la referencia a la ventana principal"""
        self._main_window = main_window

    def mousePressEvent(self, event):  # noqa: N802
        """Maneja los clics del mouse en el país"""
        if event.button() == Qt.LeftButton:
            # Clic izquierdo: seleccionar país usando el selection_manager
            if (
                self._main_window
                and hasattr(self._main_window, "scene")
                and hasattr(self._main_window.scene, "selection_manager")
            ):
                self._main_window.scene.selection_manager.seleccionar_pais(self._nombre)
        else:
            # Otros clics (como clic derecho) se manejan normalmente
            super().mousePressEvent(event)

    def set_seleccion_visual(self, tipo):
        """Establece el indicador visual de selección usando oscurecimiento"""
        # Limpiar efecto anterior si existe
        self.limpiar_seleccion_visual()

        # Aplicar efecto de oscurecimiento según el tipo
        if tipo == "origen":
            # Origen: ligeramente más oscuro (opacidad 0.7)
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.7)
            self.setGraphicsEffect(effect)
        elif tipo == "destino":
            # Destino: más oscuro (opacidad 0.5)
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.5)
            self.setGraphicsEffect(effect)

    def limpiar_seleccion_visual(self):
        """Elimina el indicador visual de selección"""
        if self.graphicsEffect():
            self.setGraphicsEffect(None)
