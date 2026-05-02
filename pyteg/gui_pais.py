"""Módulo para el widget gráfico de país en el mapa."""

from __future__ import annotations

import pathlib
from typing import Any

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsOpacityEffect,
    QGraphicsPixmapItem,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
)

from pyteg.exception import ImagenNoEncontradaError
from pyteg.gui_circulo import Circulo
from pyteg.gui_pais_battle_fx import PaisBattleFxMixin


class Pais(PaisBattleFxMixin, QGraphicsPixmapItem):
    """Widget gráfico que representa un país en el mapa."""

    def __init__(
        self, path: str, pais: tuple[str, str], pos: tuple[float, float, float, float]
    ) -> None:
        """Inicializa el widget de país.

        Args:
            path: Ruta a la imagen del país.
            pais: Tupla con (nombre del país, continente).
            pos: Tupla con (x, y, army_x, army_y) para posicionamiento.

        Raises:
            ImagenNoEncontradaError: Si la imagen no existe o no se puede cargar.

        """
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
        self._circle: Circulo | None = None
        self._center_text: QGraphicsTextItem | None = None
        self._main_window: Any = None

        # Variables para efectos de batalla (ver PaisBattleFxMixin)
        self._titilacion_timer: QTimer | None = None
        self._titilacion_effect: QGraphicsColorizeEffect | None = None
        self._titilacion_intensidad = 0.0
        self._titilacion_direccion = 1
        self._perdida_flotante: QGraphicsTextItem | None = None

        self._misiles_text: QGraphicsTextItem | None = None
        self._cantidad_misiles = 0

        self._opacity_animation: QPropertyAnimation | None = None
        self._movimiento_timer: QTimer | None = None

        self.cargar_circulo()

    def cargar_circulo(self) -> None:
        """Carga y posiciona el círculo que muestra las unidades."""
        pos_x_abs = self._army_x
        pos_y_abs = self._army_y
        # (x, y)
        self._circle = Circulo(pos_x_abs, pos_y_abs)
        self._circle.setParentItem(self)

    def nombre(self) -> str:
        """Obtiene el nombre del país.

        Returns:
            Nombre del país.

        """
        return self._nombre

    def set_color(self, color: QColor | str | None) -> None:
        """Establece el color del país.

        Args:
            color: Color a establecer (QColor, string hexadecimal o None).

        """
        if color and self._circle:
            self._circle.set_color(color)

    def set_unidades(self, cant: int | str) -> None:
        """Establece la cantidad de unidades en el país.

        Args:
            cant: Cantidad de unidades (int o string).

        """
        if self._circle:
            self._circle.set_unidades(cant)

    def get_unidades(self) -> int:
        """Retorna la cantidad de unidades como entero.

        Returns:
            Cantidad de unidades como entero.

        """
        if self._circle:
            return self._circle.get_unidades()
        return 0

    def set_main_window(self, main_window: Any) -> None:
        """Establece la referencia a la ventana principal."""
        self._main_window = main_window

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja los clics del mouse en el país."""
        if event.button() == Qt.MouseButton.LeftButton:
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

    def set_seleccion_visual(self, tipo: str) -> None:
        """Establece el indicador visual de selección usando oscurecimiento."""
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

    def limpiar_seleccion_visual(self) -> None:
        """Elimina el indicador visual de selección."""
        if self.graphicsEffect():
            self.setGraphicsEffect(None)  # type: ignore[arg-type]
