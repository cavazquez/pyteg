"""Módulo para el widget gráfico de país en el mapa."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
)

from pyteg.exceptions import ImagenNoEncontradaError
from pyteg.gui.mapa.pais_battle_fx_mixin import PaisBattleFxMixin
from pyteg.gui.mapa.pais_selection_mixin import PaisSelectionMixin
from pyteg.gui.widgets.circulo import Circulo

if TYPE_CHECKING:
    from PySide6.QtCore import QPropertyAnimation, QTimer


class Pais(PaisBattleFxMixin, PaisSelectionMixin, QGraphicsPixmapItem):
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
