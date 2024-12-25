from pathlib import Path

from PySide6.QtGui import (
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
)

from src.gui_menu import Menu
from src.gui_pais import Pais
from src.toml_reader import TomlReader


class QCustomGraphicsScene(QGraphicsScene):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.paises = {}
        self.load_map_data()

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        # Obtener las coordenadas del mouse en la escena
        # Mostrar las coordenadas en el Status Bar
        scene_pos = event.scenePos()
        self.main_window.update_status_bar(
            f"Coordenadas: ({scene_pos.x()}, {scene_pos.y()})",
        )
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QMouseEvent):  # noqa: N802
        self.main_window.clear_status_bar()
        super().leaveEvent(event)

    def contextMenuEvent(self, event):  # noqa: N802
        # Verificar si se hizo clic derecho sobre el QGraphicsPixmapItem
        items = self.items(event.scenePos())
        for item in items:
            if isinstance(item, QGraphicsPixmapItem):
                pais = item.nombre()
                Menu(pais).exec_(event.screenPos())

    def load_map_data(self):
        folder = "themes/"

        reader = TomlReader(
            Path("themes/test/paises.toml").read_text(encoding="locale"),
        )

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                # Paises
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                x = cor_x + pos_x
                y = cor_y + pos_y
                abs_img_path = folder + reader.img_path(pais)
                pixmap_item = Pais(
                    abs_img_path,
                    (pais, continente),
                    (x, y, army_x, army_y),
                )
                self.paises[pais] = pixmap_item
                self.addItem(pixmap_item)
