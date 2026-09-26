"""Módulo para la escena gráfica del mapa del juego."""

from __future__ import annotations

from operator import itemgetter
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSceneMouseEvent,
    QMenu,
    QWidget,
)

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.core.mapa.theme_layout import ThemeVisualConnection
from pyteg.gui.mapa.landmass_layers import add_landmass_layers
from pyteg.gui.mapa.menu import Menu
from pyteg.gui.mapa.overlap_check import (
    PaisBounds,
    load_pais_bounds,
    paises_en_punto,
)
from pyteg.gui.mapa.pais import Pais
from pyteg.gui.mapa.selection_manager import CountrySelectionManager
from pyteg.gui.mapa.visual_connections import add_visual_connections
from pyteg.i18n import translate as _
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from PySide6.QtSvgWidgets import QGraphicsSvgItem


class QCustomGraphicsScene(QGraphicsScene):
    """Escena gráfica personalizada para mostrar el mapa del juego."""

    def __init__(
        self,
        main_window: Any,
        parent: QWidget | None = None,
        *,
        theme: str = DEFAULT_MAP_THEME,
    ) -> None:
        """Inicializa la escena gráfica.

        Args:
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional).
            theme: Nombre del tema de mapa en themes/.

        """
        super().__init__(parent)
        self.main_window = main_window
        self.map_theme = theme
        self.paises: dict[str, Pais] = {}
        self.visual_connections: list[QGraphicsPathItem] = []
        self.connection_hints: list[QGraphicsPathItem] = []
        self._adjacencies: dict[str, list[str]] = {}
        self._visual_route_by_pair: dict[frozenset[str], ThemeVisualConnection] = {}
        self.landmass_shells: list[QGraphicsSvgItem] = []
        self.landmass_borders: list[QGraphicsSvgItem] = []
        self.setBackgroundBrush(QBrush(QColor("#87CEEB")))
        self.selection_manager = CountrySelectionManager(main_window, self)
        self.load_map_data(theme=theme)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja el movimiento del mouse en la escena.

        Args:
            event: Evento de movimiento del mouse.

        """
        # Obtener las coordenadas del mouse en la escena
        # Mostrar las coordenadas en el Status Bar
        scene_pos = event.scenePos()
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if not hasattr(self, "_debug_bounds"):
                self._debug_bounds = load_pais_bounds(self.map_theme)
            stack = paises_en_punto(self._debug_bounds, scene_pos.x(), scene_pos.y())
            if stack:
                msg = _("Bajo cursor: {}").format(" → ".join(stack))
            else:
                msg = _("Coordenadas: ({}, {}) — sin país").format(
                    scene_pos.x(), scene_pos.y()
                )
        else:
            paises_bajo_cursor = [
                item for item in self.items(scene_pos) if isinstance(item, Pais)
            ]
            if paises_bajo_cursor:
                pais = paises_bajo_cursor[0]
                superpuestos = len(paises_bajo_cursor) - 1
                extra = (
                    _(" | Países superpuestos: {}").format(superpuestos)
                    if superpuestos
                    else ""
                )
                msg = _(
                    "País: {pais} | Continente: {continente} | "
                    "Unidades: {unidades}{extra}"
                ).format(
                    pais=pais.nombre(),
                    continente=pais.continente(),
                    unidades=pais.get_unidades(),
                    extra=extra,
                )
            else:
                msg = _("Coordenadas: ({}, {})").format(scene_pos.x(), scene_pos.y())
        status_manager = getattr(self.main_window, "status_manager", None)
        update_hover = getattr(status_manager, "update_hover", None)
        if callable(update_hover):
            update_hover(msg)
        else:
            self.main_window.update_status_bar(msg)
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja los clics del mouse en la escena."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            if self._handle_country_click(scene_pos, event.screenPos()):
                event.accept()
                return

            items = self.items(scene_pos)
            pais_clicked = any(isinstance(item, Pais) for item in items)
            if not pais_clicked:
                self.selection_manager.cancelar_seleccion()

        super().mousePressEvent(event)

    def _ensure_bounds_cache(self) -> list[PaisBounds]:
        if not hasattr(self, "_debug_bounds"):
            self._debug_bounds = load_pais_bounds(self.map_theme)
        return self._debug_bounds

    def handle_country_click(
        self, scene_pos: QPointF, screen_pos: QPoint | None = None
    ) -> bool:
        """Resuelve clic en país(es); menú si hay superposición.

        Returns:
            True si el clic fue consumido.

        """
        from PySide6.QtGui import QCursor  # noqa: PLC0415

        pos = scene_pos
        x = float(pos.x())
        y = float(pos.y())
        stack = paises_en_punto(self._ensure_bounds_cache(), x, y)
        if not stack:
            return False

        if len(stack) == 1:
            self.selection_manager.seleccionar_pais(stack[0])
            return True

        menu = QMenu(self.main_window)
        menu.setTitle(_("Seleccionar país"))
        for nombre in stack:
            action = menu.addAction(nombre)
            action.triggered.connect(
                lambda _checked=False, n=nombre: (
                    self.selection_manager.seleccionar_pais(n)
                )
            )
        global_pos = screen_pos if screen_pos is not None else QCursor.pos()
        try:
            menu.exec(global_pos)
        finally:
            menu.deleteLater()
        return True

    def _handle_country_click(self, scene_pos: QPointF, screen_pos: QPoint) -> bool:
        return self.handle_country_click(scene_pos, screen_pos)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:  # noqa: N802
        """Maneja el menú contextual (clic derecho) en la escena.

        Args:
            event: Evento de menú contextual.

        """
        selection_manager = self.selection_manager
        seleccion_completa = (
            selection_manager.get_pais_origen() is not None
            and selection_manager.get_pais_destino() is not None
        )
        pos = event.scenePos()
        paises_bajo_cursor = [
            nombre
            for nombre in paises_en_punto(
                self._ensure_bounds_cache(), float(pos.x()), float(pos.y())
            )
            if nombre in self.paises
        ]

        menu: QMenu
        if seleccion_completa:
            pais = paises_bajo_cursor[0] if len(paises_bajo_cursor) == 1 else None
            continente = self.paises[pais].continente() if pais is not None else None
            menu = Menu(
                pais,
                continente,
                self.main_window,
                parent=self.main_window,
                solo_seleccion=True,
            )
            if len(paises_bajo_cursor) > 1:
                menu.addSeparator()
                paises_menu = menu.addMenu(_("Países bajo cursor"))
                self._agregar_submenus_paises(
                    paises_menu, paises_bajo_cursor, solo_pais=True
                )
        elif len(paises_bajo_cursor) == 1:
            pais = paises_bajo_cursor[0]
            # Pasar explícitamente la ventana principal como padre para Wayland.
            menu = Menu(
                pais,
                self.paises[pais].continente(),
                self.main_window,
                parent=self.main_window,
            )
        elif paises_bajo_cursor:
            menu = QMenu(_("Seleccionar país"), self.main_window)
            self._agregar_submenus_paises(menu, paises_bajo_cursor)
        else:
            event.ignore()
            return

        try:
            menu.exec_(event.screenPos())
        finally:
            menu.deleteLater()
        event.accept()

    def _agregar_submenus_paises(
        self, menu: QMenu, nombres: list[str], *, solo_pais: bool = False
    ) -> None:
        """Ofrece las acciones de cada país en el mismo orden del clic izquierdo."""
        for nombre in nombres:
            pais_menu = Menu(
                nombre,
                self.paises[nombre].continente(),
                self.main_window,
                parent=menu,
                solo_pais=solo_pais,
            )
            pais_menu.setTitle(nombre)
            menu.addMenu(pais_menu)

    def load_map_data(self, theme: str = DEFAULT_MAP_THEME) -> None:
        """Carga los datos del mapa desde archivos TOML y crea los widgets de países."""
        folder = "themes/"
        reader = TomlReader.from_theme(theme, strict=True)
        if theme == "revancha":
            self._adjacencies = reader.adyacencias
            self._visual_route_by_pair = {
                frozenset((connection.origen, connection.destino)): connection
                for connection in reader.get_conexiones_visuales()
            }

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                # Paises
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                x = cor_x + pos_x
                y = cor_y + pos_y
                abs_img_path = str(get_resource_path(folder + reader.img_path(pais)))
                pixmap_item = Pais(
                    abs_img_path,
                    (pais, continente),
                    (x, y, army_x, army_y),
                )
                # Establecer la referencia a la ventana principal
                pixmap_item.set_main_window(self.main_window)
                self.paises[pais] = pixmap_item
                self.addItem(pixmap_item)

        self.landmass_shells, self.landmass_borders = add_landmass_layers(self, theme)
        self.visual_connections = add_visual_connections(
            self, reader.get_conexiones_visuales(), self.paises, theme=theme
        )
        self._apply_country_z_order()
        self._elevate_army_markers()

    def refresh_revancha_connection_hints(self, origin: str | None) -> None:
        """Highlight all playable neighbors of the selected Revancha country."""
        for item in self.connection_hints:
            self.removeItem(item)
        self.connection_hints.clear()
        if self.map_theme != "revancha" or origin not in self._adjacencies:
            return

        connections: list[ThemeVisualConnection] = []
        for neighbor in sorted(self._adjacencies[origin]):
            country = self.paises[neighbor]
            outline = QGraphicsPathItem(country.mapToScene(country.shape()))
            pen = QPen(QColor("#b45b12"))
            pen.setWidthF(3.2)
            pen.setCosmetic(True)
            outline.setPen(pen)
            outline.setZValue(95.0)
            outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            outline.setToolTip(
                _("Conexión jugable: {origen} ↔ {destino}").format(
                    origen=origin, destino=neighbor
                )
            )
            self.addItem(outline)
            self.connection_hints.append(outline)

            pair = frozenset((origin, neighbor))
            connections.append(
                self._visual_route_by_pair.get(
                    pair, ThemeVisualConnection(origen=origin, destino=neighbor)
                )
            )

        self.connection_hints.extend(
            add_visual_connections(
                self,
                connections,
                self.paises,
                theme="revancha",
                highlight=True,
            )
        )

    def _apply_country_z_order(self) -> None:
        """Países más pequeños quedan encima para facilitar el clic."""
        areas: list[tuple[str, int]] = []
        for nombre, widget in self.paises.items():
            pixmap = widget.pixmap()
            areas.append((nombre, pixmap.width() * pixmap.height()))
        areas.sort(key=itemgetter(1))
        for z_index, (nombre, _area) in enumerate(areas):
            self.paises[nombre].setZValue(z_index)

    def _elevate_army_markers(self) -> None:
        """Dibuja los círculos de unidades por encima de países vecinos superpuestos."""
        z_marker = 1000
        for pais in self.paises.values():
            circle = getattr(pais, "_circle", None)
            if circle is None:
                continue
            scene_pos = pais.mapToScene(circle.pos())
            circle.setParentItem(None)
            circle.setPos(scene_pos)
            circle.setZValue(z_marker)
            circle.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            z_marker += 1

    def obtener_pais(self, nombre_pais: str) -> Pais | None:
        """Retorna el widget del país especificado.

        Args:
            nombre_pais (str): Nombre del país a buscar

        Returns:
            Pais | None: Widget del país o None si no existe

        """
        return self.paises.get(nombre_pais)
