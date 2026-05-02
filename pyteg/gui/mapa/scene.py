"""Módulo para la escena gráfica del mapa del juego."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
)
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSceneMouseEvent,
    QWidget,
)

from pyteg.gui.mapa.selection_manager import CountrySelectionManager
from pyteg.gui_menu import Menu
from pyteg.gui_pais import Pais
from pyteg.i18n import translate as _
from pyteg.toml_reader import TomlReader
from pyteg.utils import get_resource_path


class QCustomGraphicsScene(QGraphicsScene):
    """Escena gráfica personalizada para mostrar el mapa del juego."""

    def __init__(self, main_window: Any, parent: QWidget | None = None) -> None:
        """Inicializa la escena gráfica.

        Args:
            main_window: Ventana principal de la aplicación.
            parent: Widget padre (opcional).

        """
        super().__init__(parent)
        self.main_window = main_window
        self.paises: dict[str, Pais] = {}
        # Configurar fondo celeste que representa el agua/océano
        self.setBackgroundBrush(QBrush(QColor("#87CEEB")))  # Sky Blue / Celeste suave
        # Crear el manejador de selección de países
        self.selection_manager = CountrySelectionManager(main_window, self)
        self.load_map_data()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja el movimiento del mouse en la escena.

        Args:
            event: Evento de movimiento del mouse.

        """
        # Obtener las coordenadas del mouse en la escena
        # Mostrar las coordenadas en el Status Bar
        scene_pos = event.scenePos()
        self.main_window.update_status_bar(
            _("Coordenadas: ({}, {})").format(scene_pos.x(), scene_pos.y()),
        )
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        """Maneja los clics del mouse en la escena.

        Args:
            event: Evento de clic del mouse.

        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Verificar si se hizo clic en un área vacía (sin países)
            items = self.items(event.scenePos())
            pais_clicked = any(isinstance(item, Pais) for item in items)

            # Si no se hizo clic en un país, cancelar todas las selecciones
            if not pais_clicked:
                self.selection_manager.cancelar_seleccion()

        # Llamar al evento original para mantener funcionalidad existente
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:  # noqa: N802
        """Maneja el menú contextual (clic derecho) en la escena.

        Args:
            event: Evento de menú contextual.

        """
        # Verificar si se hizo clic derecho sobre el QGraphicsPixmapItem
        items = self.items(event.scenePos())
        for item in items:
            if isinstance(item, Pais):
                pais = item.nombre()
                # Pasar explícitamente la ventana principal como padre para Wayland
                menu = Menu(pais, self.main_window, parent=self.main_window)
                menu.exec_(event.screenPos())

    def load_map_data(self) -> None:
        """Carga los datos del mapa desde archivos TOML y crea los widgets de países."""
        folder = "themes/"

        paises_content = get_resource_path("themes/classic/paises.toml").read_text(
            encoding="utf-8"
        )
        cartas_content = get_resource_path("themes/classic/cartas.toml").read_text(
            encoding="utf-8"
        )
        adyacencias_content = get_resource_path(
            "themes/classic/adyacencias.toml"
        ).read_text(encoding="utf-8")
        reader = TomlReader(paises_content, cartas_content, adyacencias_content)

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

    def obtener_pais(self, nombre_pais: str) -> Pais | None:
        """Retorna el widget del país especificado.

        Args:
            nombre_pais (str): Nombre del país a buscar

        Returns:
            Pais | None: Widget del país o None si no existe

        """
        return self.paises.get(nombre_pais)
