"""Módulo para el widget gráfico de país en el mapa."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Any, cast

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
)

from pyteg.exceptions import ImagenNoEncontradaError
from pyteg.gui.mapa.army_position import resolve_army_position
from pyteg.gui.mapa.country_label import CountryLabel
from pyteg.gui.mapa.pais_battle_fx_mixin import PaisBattleFxMixin
from pyteg.gui.mapa.pais_selection_mixin import PaisSelectionMixin
from pyteg.gui.widgets.circulo import Circulo

if TYPE_CHECKING:
    from PySide6.QtCore import QPropertyAnimation, QTimer
    from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget


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

        """
        pixmap, svg_renderer, asset_path = self._load_asset(path, pais)

        super().__init__(pixmap)
        self._svg_renderer = svg_renderer
        self._asset_path = asset_path
        self._nombre, self._continente = pais
        self._x, self._y, self._army_x, self._army_y = pos
        self.setPos(self._x, self._y)
        self._circle: Circulo | None = None
        self._country_label = CountryLabel(self._nombre, self)
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

        self.setAcceptHoverEvents(True)
        self._position_country_label()
        self.cargar_circulo()
        self._actualizar_tooltip()

    def _position_country_label(self) -> None:
        """Centra el nombre dentro del asset sin mover su posición lógica."""
        bounds = self._country_label.boundingRect()
        pixmap = self.pixmap()
        self._country_label.setPos(
            (pixmap.width() - bounds.width()) / 2,
            (
                max(0.0, pixmap.height() - bounds.height() - 2)
                if self._army_y < pixmap.height() / 2
                else 2.0
            ),
        )

    def hoverEnterEvent(self, event: Any) -> None:  # noqa: N802
        """Muestra el nombre completo al entrar con el cursor."""
        self._country_label.set_hovered(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:  # noqa: N802
        """Vuelve a la política de zoom al salir con el cursor."""
        self._country_label.set_hovered(False)
        super().hoverLeaveEvent(event)

    @staticmethod
    def _load_asset(
        path: str, pais: tuple[str, str]
    ) -> tuple[QPixmap, QSvgRenderer | None, str]:
        """Carga un asset raster o vectorial manteniendo una imagen base.

        ``QGraphicsPixmapItem`` sigue siendo la superficie de interacción y
        conserva sus bounds, efectos y z-order. Para SVG se crea además una
        imagen transparente del tamaño del ``viewBox``; el método ``paint``
        vuelve a dibujar el renderer vectorial en cada escala, de modo que el
        asset no se pixela al hacer zoom. Si un SVG todavía no puede abrirse,
        se intenta el PNG con el mismo nombre como fallback de distribución.

        Returns:
            Pixmap base, renderer SVG opcional y ruta efectiva.

        Raises:
            ImagenNoEncontradaError: Si no existe un asset cargable.

        """
        requested = pathlib.Path(path)
        candidates = [requested]
        if requested.suffix.lower() == ".svg":
            candidates.append(requested.with_suffix(".png"))

        for candidate in candidates:
            if not candidate.exists():
                continue

            if candidate.suffix.lower() == ".svg":
                renderer = QSvgRenderer(str(candidate))
                if not renderer.isValid():
                    continue
                size = renderer.defaultSize()
                if not size.isValid() or size.width() <= 0 or size.height() <= 0:
                    view_box = renderer.viewBoxF()
                    size = QSize(round(view_box.width()), round(view_box.height()))
                if size.width() <= 0 or size.height() <= 0:
                    continue

                image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(Qt.GlobalColor.transparent)
                painter = QPainter(image)
                try:
                    renderer.render(painter)
                finally:
                    painter.end()
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull():
                    return pixmap, renderer, str(candidate)
                continue

            pixmap = QPixmap(str(candidate))
            if not pixmap.isNull():
                return pixmap, None, str(candidate)

        raise ImagenNoEncontradaError(
            path,
            f"la imagen del país {pais[0]} no se pudo cargar (formato inválido)",
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Dibuja SVG a resolución vectorial y conserva el camino raster."""
        if self._svg_renderer is None:
            super().paint(painter, option, cast("QWidget", widget))
            return
        self._svg_renderer.render(painter, QRectF(self.boundingRect()))

    @property
    def es_vectorial(self) -> bool:
        """Indica si el país se está dibujando desde un SVG válido."""
        return self._svg_renderer is not None

    @property
    def ruta_asset(self) -> str:
        """Ruta efectiva del asset, útil para diagnóstico y smoke tests."""
        return self._asset_path

    def _actualizar_tooltip(self) -> None:
        """Mantiene el nombre, continente y unidades accesibles al pasar el cursor."""
        self.setToolTip(
            f"País: {self._nombre}\n"
            f"Continente: {self._continente}\n"
            f"Unidades: {self.get_unidades()}"
        )

    def cargar_circulo(self) -> None:
        """Carga y posiciona el círculo que muestra las unidades."""
        pixmap = self.pixmap()
        pos_x_abs, pos_y_abs = resolve_army_position(
            pixmap.width(),
            pixmap.height(),
            self._army_x,
            self._army_y,
        )
        self._circle = Circulo(pos_x_abs, pos_y_abs)
        self._circle.setParentItem(self)

    def nombre(self) -> str:
        """Obtiene el nombre del país.

        Returns:
            Nombre del país.

        """
        return self._nombre

    def continente(self) -> str:
        """Obtiene el identificador de continente del mapa (TOML).

        Returns:
            Nombre del continente (ej. ``Sudamerica``, ``Africa``).

        """
        return self._continente

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
            self._actualizar_tooltip()

    def get_unidades(self) -> int:
        """Retorna la cantidad de unidades como entero.

        Returns:
            Cantidad de unidades como entero.

        """
        if self._circle:
            return self._circle.get_unidades()
        return 0

    def get_cantidad_misiles(self) -> int:
        """Retorna la cantidad de misiles en el país.

        Returns:
            Cantidad de misiles disponibles.

        """
        return self._cantidad_misiles

    def set_main_window(self, main_window: Any) -> None:
        """Establece la referencia a la ventana principal."""
        self._main_window = main_window
